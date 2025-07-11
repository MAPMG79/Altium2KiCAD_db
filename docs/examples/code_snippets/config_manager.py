import json
import yaml
import configparser
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import logging
from dataclasses import dataclass, asdict

@dataclass
class MigrationConfig:
    """Configuration settings for migration"""
    # Input settings
    altium_dblib_path: str = ""
    altium_db_type: str = "auto"  # auto, access, sqlserver, mysql, postgresql, sqlite
    connection_timeout: int = 30
    
    # Output settings
    output_directory: str = ""
    database_name: str = "components.db"
    dblib_name: str = "components.kicad_dbl"
    
    # KiCAD library paths
    kicad_symbol_libraries: List[str] = None
    kicad_footprint_libraries: List[str] = None
    
    # Mapping settings
    enable_fuzzy_matching: bool = True
    fuzzy_threshold: float = 0.7
    enable_ml_matching: bool = False
    enable_semantic_matching: bool = True
    
    # Performance settings
    enable_parallel_processing: bool = True
    max_worker_threads: int = 4
    batch_size: int = 1000
    enable_caching: bool = True
    cache_directory: str = ".cache"
    
    # Database settings
    create_indexes: bool = True
    create_views: bool = True
    vacuum_database: bool = True
    
    # Field mapping
    custom_field_mappings: Dict[str, str] = None
    excluded_fields: List[str] = None
    
    # Validation settings
    validate_symbols: bool = False
    validate_footprints: bool = False
    confidence_threshold: float = 0.5
    
    # Logging settings
    log_level: str = "INFO"
    log_file: str = "migration.log"
    enable_progress_tracking: bool = True
    
    def __post_init__(self):
        if self.kicad_symbol_libraries is None:
            self.kicad_symbol_libraries = []
        if self.kicad_footprint_libraries is None:
            self.kicad_footprint_libraries = []
        if self.custom_field_mappings is None:
            self.custom_field_mappings = {}
        if self.excluded_fields is None:
            self.excluded_fields = []

class ConfigurationManager:
    """Manage migration configuration settings"""
    
    def __init__(self, config_path: str = "migration_config.yaml"):
        self.config_path = Path(config_path)
        self.config = MigrationConfig()
        self.load_config()
    
    def load_config(self) -> MigrationConfig:
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    if self.config_path.suffix.lower() == '.yaml':
                        config_data = yaml.safe_load(f)
                    elif self.config_path.suffix.lower() == '.json':
                        config_data = json.load(f)
                    else:
                        # Try INI format
                        config_parser = configparser.ConfigParser()
                        config_parser.read(self.config_path)
                        config_data = {section: dict(config_parser[section]) 
                                      for section in config_parser.sections()}
                
                # Update configuration with loaded data
                self._update_config(config_data)
                
                logging.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logging.error(f"Error loading configuration: {e}")
                # Use default configuration
        else:
            logging.warning(f"Configuration file {self.config_path} not found, using defaults")
        
        return self.config
    
    def _update_config(self, config_data: Dict[str, Any]) -> None:
        """Update configuration with loaded data"""
        # Flatten nested configuration if needed
        flat_config = {}
        for key, value in config_data.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    flat_config[f"{key}_{subkey}"] = subvalue
            else:
                flat_config[key] = value
        
        # Update configuration fields
        for key, value in flat_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            config_data = asdict(self.config)
            
            with open(self.config_path, 'w') as f:
                if self.config_path.suffix.lower() == '.yaml':
                    yaml.dump(config_data, f, default_flow_style=False)
                elif self.config_path.suffix.lower() == '.json':
                    json.dump(config_data, f, indent=2)
                else:
                    # Save as INI format
                    config_parser = configparser.ConfigParser()
                    
                    # Group configuration by sections
                    sections = {
                        'Input': ['altium_dblib_path', 'altium_db_type', 'connection_timeout'],
                        'Output': ['output_directory', 'database_name', 'dblib_name'],
                        'Libraries': ['kicad_symbol_libraries', 'kicad_footprint_libraries'],
                        'Mapping': ['enable_fuzzy_matching', 'fuzzy_threshold', 
                                   'enable_ml_matching', 'enable_semantic_matching'],
                        'Performance': ['enable_parallel_processing', 'max_worker_threads', 
                                       'batch_size', 'enable_caching', 'cache_directory'],
                        'Database': ['create_indexes', 'create_views', 'vacuum_database'],
                        'Fields': ['custom_field_mappings', 'excluded_fields'],
                        'Validation': ['validate_symbols', 'validate_footprints', 'confidence_threshold'],
                        'Logging': ['log_level', 'log_file', 'enable_progress_tracking']
                    }
                    
                    for section, keys in sections.items():
                        config_parser[section] = {}
                        for key in keys:
                            value = getattr(self.config, key)
                            if isinstance(value, (list, dict)):
                                value = json.dumps(value)
                            config_parser[section][key] = str(value)
                    
                    config_parser.write(f)
            
            logging.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
    
    def get_config(self) -> MigrationConfig:
        """Get current configuration"""
        return self.config
    
    def update_config(self, **kwargs) -> None:
        """Update configuration with provided values"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logging.warning(f"Unknown configuration key: {key}")
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Check required paths
        if not self.config.altium_dblib_path:
            errors.append("Altium DbLib path is required")
        
        if not self.config.output_directory:
            errors.append("Output directory is required")
        
        # Check valid values
        if self.config.altium_db_type not in ["auto", "access", "sqlserver", "mysql", "postgresql", "sqlite"]:
            errors.append(f"Invalid database type: {self.config.altium_db_type}")
        
        if self.config.max_worker_threads < 1:
            errors.append(f"Invalid worker thread count: {self.config.max_worker_threads}")
        
        if self.config.batch_size < 1:
            errors.append(f"Invalid batch size: {self.config.batch_size}")
        
        if not (0.0 <= self.config.fuzzy_threshold <= 1.0):
            errors.append(f"Invalid fuzzy threshold: {self.config.fuzzy_threshold}")
        
        if not (0.0 <= self.config.confidence_threshold <= 1.0):
            errors.append(f"Invalid confidence threshold: {self.config.confidence_threshold}")
        
        return errors

# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create configuration manager
    config_manager = ConfigurationManager("example_config.yaml")
    
    # Update configuration
    config_manager.update_config(
        altium_dblib_path="path/to/library.DbLib",
        output_directory="output",
        enable_fuzzy_matching=True,
        fuzzy_threshold=0.8
    )
    
    # Validate configuration
    errors = config_manager.validate_config()
    if errors:
        for error in errors:
            logging.error(f"Configuration error: {error}")
    else:
        # Save configuration
        config_manager.save_config()
        
        # Get configuration
        config = config_manager.get_config()
        logging.info(f"Using Altium DbLib: {config.altium_dblib_path}")
        logging.info(f"Output directory: {config.output_directory}")