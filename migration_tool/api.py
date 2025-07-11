#!/usr/bin/env python3
"""
Web API Interface for Altium to KiCAD Database Migration Tool.

This module provides a FastAPI-based REST API for the migration tool.
"""

import os
import json
import uuid
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from migration_tool.core.altium_parser import AltiumDbLibParser
from migration_tool.core.mapping_engine import ComponentMappingEngine
from migration_tool.core.kicad_generator import KiCADDbLibGenerator
from migration_tool.utils.config_manager import ConfigManager
from migration_tool.utils.database_utils import create_connection
from migration_tool.utils.logging_utils import setup_logging, get_logger

# Setup logging
logger = setup_logging(log_level="INFO")

# Initialize FastAPI app
app = FastAPI(
    title="Altium to KiCAD Migration API",
    description="API for migrating Altium DbLib databases to KiCAD format",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# In-memory job storage
# In a production environment, this would be replaced with a database
jobs = {}
mapping_rules = {
    "symbol": {},
    "footprint": {},
    "category": {}
}

# Rate limiting
rate_limit = {}

# Load configuration
config_manager = ConfigManager()
try:
    config_paths = [
        "config/default_config.yaml",
        os.path.expanduser("~/.altium2kicad/config.yaml"),
        "migration_config.yaml"
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            config_manager.load_config(path)
            logger.info(f"Loaded configuration from {path}")
            break
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")


# Models
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class ConnectionConfig(BaseModel):
    db_type: str
    connection_string: str


class MappingRule(BaseModel):
    altium_value: str
    kicad_value: str


class CategoryMapping(BaseModel):
    altium_category: str
    kicad_category: str
    kicad_subcategory: Optional[str] = None
    keywords: List[str] = []


class MigrationConfig(BaseModel):
    altium_dblib_path: str
    output_directory: str = "output"
    create_views: bool = True
    include_confidence: bool = True
    validate_symbols: bool = False
    enable_parallel: bool = True
    enable_caching: bool = True
    fuzzy_threshold: float = 0.7
    max_threads: int = 4
    batch_size: int = 1000
    dry_run: bool = False
    kicad_symbol_libraries: List[str] = []
    kicad_footprint_libraries: List[str] = []


class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str
    start_time: datetime
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None


class ValidationRequest(BaseModel):
    altium_dblib_path: str
    connection_config: Optional[ConnectionConfig] = None


class ValidationResult(BaseModel):
    valid: bool
    issues: Dict[str, str] = {}
    tables: List[str] = []
    message: str


class MappingRulesList(BaseModel):
    symbol_mappings: Dict[str, str] = {}
    footprint_mappings: Dict[str, str] = {}
    category_mappings: Dict[str, Dict[str, Any]] = {}


# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # In a real application, you would validate the token against a database
    # For this example, we'll accept any token
    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    # Skip rate limiting for certain endpoints
    if request.url.path in ["/api/v1/health", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    # Check rate limit
    current_time = datetime.now()
    if client_ip in rate_limit:
        last_request_time, count = rate_limit[client_ip]
        time_diff = (current_time - last_request_time).total_seconds()
        
        # Reset count if more than 60 seconds have passed
        if time_diff > 60:
            rate_limit[client_ip] = (current_time, 1)
        # Rate limit: 30 requests per minute
        elif count >= 30:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please try again later."}
            )
        else:
            rate_limit[client_ip] = (last_request_time, count + 1)
    else:
        rate_limit[client_ip] = (current_time, 1)
    
    return await call_next(request)


# Background task for migration
async def run_migration(job_id: str, config: MigrationConfig):
    try:
        # Update job status
        jobs[job_id]["status"] = "running"
        jobs[job_id]["message"] = "Starting migration process"
        jobs[job_id]["progress"] = 0.0
        
        # Create configuration
        config_dict = config.dict()
        config_manager = ConfigManager()
        config_manager.update(config_dict)
        
        # Parse Altium database
        jobs[job_id]["message"] = "Parsing Altium database"
        jobs[job_id]["progress"] = 0.1
        
        parser = AltiumDbLibParser(config_manager)
        altium_config = parser.parse_dblib_file(config.altium_dblib_path)
        
        # Extract data
        jobs[job_id]["message"] = "Extracting component data"
        jobs[job_id]["progress"] = 0.2
        
        altium_data = parser.extract_all_data(altium_config)
        
        total_components = sum(len(table_data.get('data', [])) 
                             for table_data in altium_data.values())
        
        # Map components
        jobs[job_id]["message"] = f"Mapping {total_components} components"
        jobs[job_id]["progress"] = 0.3
        
        mapper = ComponentMappingEngine(config.kicad_symbol_libraries, config_manager)
        
        # Apply custom mapping rules if available
        if mapping_rules["symbol"]:
            mapper._symbol_mappings.update(mapping_rules["symbol"])
        if mapping_rules["footprint"]:
            mapper._footprint_mappings.update(mapping_rules["footprint"])
        if mapping_rules["category"]:
            mapper._category_mappings.update(mapping_rules["category"])
        
        all_mappings = {}
        table_count = len(altium_data)
        current_table = 0
        
        for table_name, table_data in altium_data.items():
            if 'data' in table_data and table_data['data']:
                current_table += 1
                jobs[job_id]["message"] = f"Mapping table {current_table}/{table_count}: {table_name}"
                jobs[job_id]["progress"] = 0.3 + (0.4 * (current_table / table_count))
                
                # Map components
                mappings = mapper.map_table_data(table_name, table_data)
                all_mappings[table_name] = mappings
        
        # Skip file generation for dry run
        if config.dry_run:
            jobs[job_id]["message"] = "Dry run completed. No files were created."
            jobs[job_id]["progress"] = 1.0
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["end_time"] = datetime.now()
            
            # Calculate statistics
            total_mapped = sum(len(mappings) for mappings in all_mappings.values())
            high_conf = sum(sum(1 for m in mappings if m.confidence > 0.8) for mappings in all_mappings.values())
            med_conf = sum(sum(1 for m in mappings if 0.5 <= m.confidence <= 0.8) for mappings in all_mappings.values())
            low_conf = sum(sum(1 for m in mappings if m.confidence < 0.5) for mappings in all_mappings.values())
            
            jobs[job_id]["result"] = {
                "total_components": total_components,
                "total_mapped": total_mapped,
                "high_confidence": high_conf,
                "medium_confidence": med_conf,
                "low_confidence": low_conf,
                "tables": list(all_mappings.keys())
            }
            
            return
        
        # Generate KiCAD database
        jobs[job_id]["message"] = "Generating KiCAD database library"
        jobs[job_id]["progress"] = 0.8
        
        generator = KiCADDbLibGenerator(config.output_directory, config_manager)
        result = generator.generate(all_mappings)
        
        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["message"] = "Migration completed successfully"
        jobs[job_id]["progress"] = 1.0
        jobs[job_id]["end_time"] = datetime.now()
        jobs[job_id]["result"] = {
            "database_path": result["database_path"],
            "dblib_path": result["dblib_path"],
            "output_directory": result["output_directory"],
            "total_components": total_components,
            "tables": list(all_mappings.keys())
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Migration failed: {str(e)}"
        jobs[job_id]["end_time"] = datetime.now()


# API Endpoints
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/api/v1/migrate", response_model=JobStatus)
async def start_migration(
    config: MigrationConfig,
    background_tasks: BackgroundTasks,
    token: str = Depends(get_current_user)
):
    """Start a migration job."""
    # Validate input
    if not os.path.exists(config.altium_dblib_path):
        raise HTTPException(status_code=400, detail=f"Altium DbLib file not found: {config.altium_dblib_path}")
    
    # Create job
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0.0,
        "message": "Job created",
        "start_time": datetime.now(),
        "end_time": None,
        "result": None
    }
    
    # Start background task
    background_tasks.add_task(run_migration, job_id, config)
    
    return jobs[job_id]


@app.get("/api/v1/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str, token: str = Depends(get_current_user)):
    """Get job status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]


@app.get("/api/v1/jobs/{job_id}/results")
async def get_job_results(job_id: str, token: str = Depends(get_current_user)):
    """Get job results."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if jobs[job_id]["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    if not jobs[job_id]["result"]:
        raise HTTPException(status_code=404, detail="No results available")
    
    return jobs[job_id]["result"]


@app.post("/api/v1/validate", response_model=ValidationResult)
async def validate_database(
    request: ValidationRequest,
    token: str = Depends(get_current_user)
):
    """Validate Altium database."""
    try:
        # Check if file exists
        if not os.path.exists(request.altium_dblib_path):
            return ValidationResult(
                valid=False,
                message=f"File not found: {request.altium_dblib_path}"
            )
        
        # Parse DbLib file
        parser = AltiumDbLibParser()
        altium_config = parser.parse_dblib_file(request.altium_dblib_path)
        
        # Override connection config if provided
        if request.connection_config:
            parser._connection_string = request.connection_config.connection_string
            parser._db_type = request.connection_config.db_type
        
        # Test database connection
        try:
            conn = parser.connect_to_database()
            
            # Get tables
            tables = []
            if parser._db_type == "sqlite":
                query = "SELECT name FROM sqlite_master WHERE type='table'"
                result = parser.execute_query(conn, query)
                tables = [row["name"] for row in result]
            else:
                # For other database types, try to get table list
                cursor = conn.cursor()
                tables = [table.table_name for table in cursor.tables()]
                cursor.close()
            
            conn.close()
            
            return ValidationResult(
                valid=True,
                tables=tables,
                message="Database connection successful"
            )
            
        except Exception as e:
            return ValidationResult(
                valid=False,
                message=f"Database connection failed: {str(e)}"
            )
        
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        return ValidationResult(
            valid=False,
            message=f"Validation failed: {str(e)}"
        )


@app.get("/api/v1/mapping-rules", response_model=MappingRulesList)
async def get_mapping_rules(token: str = Depends(get_current_user)):
    """Get mapping rules."""
    return {
        "symbol_mappings": mapping_rules["symbol"],
        "footprint_mappings": mapping_rules["footprint"],
        "category_mappings": mapping_rules["category"]
    }


@app.put("/api/v1/mapping-rules")
async def update_mapping_rules(
    rules: MappingRulesList,
    token: str = Depends(get_current_user)
):
    """Update mapping rules."""
    mapping_rules["symbol"] = rules.symbol_mappings
    mapping_rules["footprint"] = rules.footprint_mappings
    mapping_rules["category"] = rules.category_mappings
    
    return {"status": "success", "message": "Mapping rules updated"}


def start_api_server(host="0.0.0.0", port=8000):
    """Start the API server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Altium to KiCAD API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    args = parser.parse_args()
    print(f"Starting API server with host={args.host}, port={args.port}")
    print(f"Command line arguments: {sys.argv}")
    start_api_server(host=args.host, port=args.port)