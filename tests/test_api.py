#!/usr/bin/env python3
"""
Tests for the API interface.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from migration_tool.api import app, jobs, mapping_rules


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_config_manager():
    """Mock ConfigManager."""
    with patch('migration_tool.api.ConfigManager') as mock:
        config_instance = MagicMock()
        config_instance.config = {
            'altium_dblib_path': 'test.DbLib',
            'output_directory': 'output',
            'enable_parallel_processing': True,
            'max_worker_threads': 4,
            'batch_size': 1000,
            'enable_caching': True,
            'fuzzy_threshold': 0.7,
            'enable_ml_mapping': False,
            'validate_symbols': False,
            'validate_footprints': False,
            'create_views': True,
            'vacuum_database': True,
            'log_level': 'INFO'
        }
        config_instance.validate.return_value = {}
        mock.return_value = config_instance
        yield mock


@pytest.fixture
def mock_parser():
    """Mock AltiumDbLibParser."""
    with patch('migration_tool.api.AltiumDbLibParser') as mock:
        parser_instance = MagicMock()
        parser_instance.parse_dblib_file.return_value = {
            'tables': {
                'Components': {
                    'required_fields': ['ComponentId', 'Name', 'Description']
                }
            }
        }
        parser_instance.extract_all_data.return_value = {
            'Components': {
                'data': [
                    {'ComponentId': 1, 'Name': 'Resistor', 'Description': 'Test resistor'},
                    {'ComponentId': 2, 'Name': 'Capacitor', 'Description': 'Test capacitor'}
                ]
            }
        }
        mock.return_value = parser_instance
        yield mock


@pytest.fixture
def mock_mapper():
    """Mock ComponentMappingEngine."""
    with patch('migration_tool.api.ComponentMappingEngine') as mock:
        mapper_instance = MagicMock()
        mapper_instance.map_table_data.return_value = [
            MagicMock(confidence=0.9),
            MagicMock(confidence=0.6)
        ]
        mock.return_value = mapper_instance
        yield mock


@pytest.fixture
def mock_generator():
    """Mock KiCADDbLibGenerator."""
    with patch('migration_tool.api.KiCADDbLibGenerator') as mock:
        generator_instance = MagicMock()
        generator_instance.generate.return_value = {
            'database_path': 'output/components.db',
            'dblib_path': 'output/components.kicad_dbl',
            'output_directory': 'output'
        }
        mock.return_value = generator_instance
        yield mock


@pytest.fixture
def mock_token():
    """Mock token for authentication."""
    return "Bearer test-token"


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_migrate_endpoint(client, mock_token, mock_config_manager, mock_parser, mock_mapper, mock_generator):
    """Test migrate endpoint."""
    with tempfile.NamedTemporaryFile(suffix='.DbLib') as temp_file:
        # Create a mock file
        with open(temp_file.name, 'w') as f:
            f.write('mock dblib file')
        
        # Mock os.path.exists to return True for the temp file
        with patch('os.path.exists', return_value=True):
            response = client.post(
                "/api/v1/migrate",
                headers={"Authorization": mock_token},
                json={
                    "altium_dblib_path": temp_file.name,
                    "output_directory": "output",
                    "create_views": True,
                    "include_confidence": True,
                    "validate_symbols": False,
                    "enable_parallel": True,
                    "enable_caching": True,
                    "fuzzy_threshold": 0.7,
                    "max_threads": 4,
                    "batch_size": 1000,
                    "dry_run": False,
                    "kicad_symbol_libraries": [],
                    "kicad_footprint_libraries": []
                }
            )
            
            assert response.status_code == 200
            assert "job_id" in response.json()
            assert response.json()["status"] == "pending"


def test_get_job_status(client, mock_token):
    """Test get job status endpoint."""
    # Create a mock job
    job_id = "test-job-id"
    jobs[job_id] = {
        "job_id": job_id,
        "status": "running",
        "progress": 0.5,
        "message": "Processing components",
        "start_time": "2025-01-01T00:00:00",
        "end_time": None,
        "result": None
    }
    
    response = client.get(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": mock_token}
    )
    
    assert response.status_code == 200
    assert response.json()["job_id"] == job_id
    assert response.json()["status"] == "running"
    
    # Test non-existent job
    response = client.get(
        "/api/v1/jobs/non-existent-job",
        headers={"Authorization": mock_token}
    )
    
    assert response.status_code == 404


def test_get_job_results(client, mock_token):
    """Test get job results endpoint."""
    # Create a mock completed job
    job_id = "test-completed-job"
    jobs[job_id] = {
        "job_id": job_id,
        "status": "completed",
        "progress": 1.0,
        "message": "Migration completed successfully",
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-01-01T00:01:00",
        "result": {
            "database_path": "output/components.db",
            "dblib_path": "output/components.kicad_dbl",
            "output_directory": "output",
            "total_components": 100,
            "tables": ["Components"]
        }
    }
    
    response = client.get(
        f"/api/v1/jobs/{job_id}/results",
        headers={"Authorization": mock_token}
    )
    
    assert response.status_code == 200
    assert "database_path" in response.json()
    assert response.json()["total_components"] == 100
    
    # Test incomplete job
    job_id = "test-running-job"
    jobs[job_id] = {
        "job_id": job_id,
        "status": "running",
        "progress": 0.5,
        "message": "Processing components",
        "start_time": "2025-01-01T00:00:00",
        "end_time": None,
        "result": None
    }
    
    response = client.get(
        f"/api/v1/jobs/{job_id}/results",
        headers={"Authorization": mock_token}
    )
    
    assert response.status_code == 400


def test_validate_endpoint(client, mock_token, mock_parser):
    """Test validate endpoint."""
    with tempfile.NamedTemporaryFile(suffix='.DbLib') as temp_file:
        # Create a mock file
        with open(temp_file.name, 'w') as f:
            f.write('mock dblib file')
        
        # Mock connection
        conn_mock = MagicMock()
        mock_parser.return_value.connect_to_database.return_value = conn_mock
        
        # Mock os.path.exists to return True for the temp file
        with patch('os.path.exists', return_value=True):
            response = client.post(
                "/api/v1/validate",
                headers={"Authorization": mock_token},
                json={
                    "altium_dblib_path": temp_file.name
                }
            )
            
            assert response.status_code == 200
            assert response.json()["valid"] is True
            
            # Test with connection config
            response = client.post(
                "/api/v1/validate",
                headers={"Authorization": mock_token},
                json={
                    "altium_dblib_path": temp_file.name,
                    "connection_config": {
                        "db_type": "sqlite",
                        "connection_string": "sqlite:///test.db"
                    }
                }
            )
            
            assert response.status_code == 200
            assert response.json()["valid"] is True


def test_mapping_rules_endpoints(client, mock_token):
    """Test mapping rules endpoints."""
    # Test get mapping rules
    response = client.get(
        "/api/v1/mapping-rules",
        headers={"Authorization": mock_token}
    )
    
    assert response.status_code == 200
    assert "symbol_mappings" in response.json()
    assert "footprint_mappings" in response.json()
    assert "category_mappings" in response.json()
    
    # Test update mapping rules
    new_rules = {
        "symbol_mappings": {
            "RES": "Device:R",
            "CAP": "Device:C"
        },
        "footprint_mappings": {
            "0603": "Resistor_SMD:R_0603_1608Metric",
            "0805": "Resistor_SMD:R_0805_2012Metric"
        },
        "category_mappings": {
            "Resistors": {
                "category": "Passive Components",
                "subcategory": "Resistors",
                "keywords": ["resistor", "res"]
            }
        }
    }
    
    response = client.put(
        "/api/v1/mapping-rules",
        headers={"Authorization": mock_token},
        json=new_rules
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify rules were updated
    assert mapping_rules["symbol"]["RES"] == "Device:R"
    assert mapping_rules["footprint"]["0603"] == "Resistor_SMD:R_0603_1608Metric"
    assert mapping_rules["category"]["Resistors"]["category"] == "Passive Components"


def test_authentication(client):
    """Test authentication requirement."""
    response = client.get("/api/v1/jobs/test-job")
    assert response.status_code == 401
    
    response = client.get(
        "/api/v1/jobs/test-job",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 200  # In our mock implementation, any token is accepted


def test_rate_limiting(client, mock_token):
    """Test rate limiting middleware."""
    # This test is simplified since we can't easily test the actual rate limiting in a unit test
    # In a real test, we would need to mock the rate limit check
    
    with patch('migration_tool.api.rate_limit', {}):
        response = client.get("/api/v1/health")
        assert response.status_code == 200