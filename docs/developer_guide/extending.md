# Extending the Tool

This guide explains how to extend the Altium to KiCAD Database Migration Tool with new features, database support, custom mapping algorithms, and more. The tool is designed with extensibility in mind, providing clear extension points and a modular architecture.

## Extension Points Overview

The tool provides several key extension points:

1. **Database Adapters**: Add support for new database types
2. **Mapping Algorithms**: Implement custom component mapping strategies
3. **Output Generators**: Create new output formats
4. **Validation Rules**: Add custom validation logic
5. **User Interfaces**: Create alternative user interfaces
6. **Plugins**: Develop plugins for additional functionality

## Adding Database Support

### Creating a New Database Adapter

To add support for a new database type, create a new adapter class that inherits from the `DatabaseAdapter` base class:

```python
from migration_tool.core.altium_parser import DatabaseAdapter
from migration_tool.utils.logging_utils import setup_logger

@DatabaseAdapter.register("new_db_type")
class NewDatabaseAdapter(DatabaseAdapter):
    """
    Adapter for NewDB database type.
    """
    
    def __init__(self, connection_params, logger=None):
        """
        Initialize the adapter.
        
        Args:
            connection_params: Connection parameters
            logger: Optional logger instance
        """
        self.connection_params = connection_params
        self.logger = logger or setup_logger(__name__)
        self.connection = None
        
    def connect(self):
        """
        Establish a connection to the database.
        
        Returns:
            Database connection object
        
        Raises:
            ConnectionError: If connection fails
        """
        self.logger.info(f"Connecting to NewDB database: {self.connection_params['server']}")
        
        try:
            # Implement connection logic for your database
            import newdb_driver
            
            self.connection = newdb_driver.connect(
                server=self.connection_params.get('server'),
                port=self.connection_params.get('port'),
                username=self.connection_params.get('username'),
                password=self.connection_params.get('password'),
                database=self.connection_params.get('database')
            )
            
            self.logger.info("Connection established successfully")
            return self.connection
            
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
            raise ConnectionError(f"Failed to connect to NewDB database: {str(e)}")
    
    def execute_query(self, query, params=None):
        """
        Execute a query on the database.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query results
            
        Raises:
            QueryError: If query execution fails
        """
        if not self.connection:
            self.connect()
            
        try:
            # Implement query execution logic
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            results = cursor.fetchall()
            cursor.close()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            raise QueryError(f"Failed to execute query: {str(e)}")
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Connection closed")
```

### Registering the Adapter

The `@DatabaseAdapter.register("new_db_type")` decorator registers your adapter with the system. Users can then use your adapter by specifying the database type:

```yaml
input:
  database_type: new_db_type
  server: example.com
  port: 1234
  username: user
  password: pass
  database: my_db
```

### Testing the Adapter

Create tests for your adapter to ensure it works correctly:

```python
# tests/unit/test_new_database_adapter.py
import pytest
from migration_tool.core.altium_parser import get_database_adapter
from migration_tool.exceptions import ConnectionError

def test_adapter_registration():
    """Test that the adapter is properly registered."""
    adapter_class = get_database_adapter("new_db_type")
    assert adapter_class.__name__ == "NewDatabaseAdapter"

def test_adapter_connection(mocker):
    """Test adapter connection logic."""
    # Mock the database driver
    mock_driver = mocker.patch("newdb_driver.connect")
    mock_connection = mocker.MagicMock()
    mock_driver.return_value = mock_connection
    
    # Create adapter
    adapter_class = get_database_adapter("new_db_type")
    adapter = adapter_class({
        'server': 'test_server',
        'port': 1234,
        'username': 'test_user',
        'password': 'test_pass',
        'database': 'test_db'
    })
    
    # Test connection
    connection = adapter.connect()
    
    # Verify
    assert connection == mock_connection
    mock_driver.assert_called_once_with(
        server='test_server',
        port=1234,
        username='test_user',
        password='test_pass',
        database='test_db'
    )
```

## Implementing Custom Mapping Algorithms

### Creating a Custom Mapper

To implement a custom mapping algorithm, create a new mapper class that inherits from the appropriate base mapper:

```python
from migration_tool.core.mapping_engine import SymbolMapper
from migration_tool.utils.logging_utils import setup_logger

class MachineLearningSymbolMapper(SymbolMapper):
    """
    Symbol mapper that uses machine learning for improved accuracy.
    """
    
    def __init__(self, config, logger=None):
        """
        Initialize the mapper.
        
        Args:
            config: Mapping configuration
            logger: Optional logger instance
        """
        super().__init__(config, logger)
        self.logger = logger or setup_logger(__name__)
        self.model = None
        
        # Load ML model
        self._load_model()
        
    def _load_model(self):
        """Load the machine learning model."""
        try:
            import joblib
            model_path = self.config.get('ml_model_path', 'models/symbol_mapper.pkl')
            self.logger.info(f"Loading ML model from {model_path}")
            self.model = joblib.load(model_path)
        except Exception as e:
            self.logger.warning(f"Failed to load ML model: {str(e)}. Falling back to rule-based mapping.")
            self.model = None
    
    def map_symbol(self, component):
        """
        Map an Altium symbol to a KiCAD symbol using machine learning.
        
        Args:
            component: Component to map
            
        Returns:
            Tuple of (mapped_symbol, confidence_score)
        """
        # If model failed to load, fall back to parent implementation
        if self.model is None:
            return super().map_symbol(component)
            
        # Extract features for ML model
        features = self._extract_features(component)
        
        # Get predictions from model
        try:
            predictions = self.model.predict_proba([features])[0]
            symbol_idx = predictions.argmax()
            confidence = predictions[symbol_idx]
            
            # Get symbol name from index
            symbol_name = self.model.classes_[symbol_idx]
            
            self.logger.debug(f"ML mapped '{component.get('LibRef')}' to '{symbol_name}' with confidence {confidence:.2f}")
            
            return symbol_name, float(confidence)
            
        except Exception as e:
            self.logger.error(f"ML mapping failed: {str(e)}. Falling back to rule-based mapping.")
            return super().map_symbol(component)
    
    def _extract_features(self, component):
        """
        Extract features from a component for the ML model.
        
        Args:
            component: Component to extract features from
            
        Returns:
            Feature vector
        """
        # Implement feature extraction logic
        # This will depend on your ML model and the component data
        features = []
        
        # Example features
        features.append(len(component.get('LibRef', '')))
        features.append(len(component.get('Description', '')))
        features.append(1 if 'resistor' in component.get('Description', '').lower() else 0)
        features.append(1 if 'capacitor' in component.get('Description', '').lower() else 0)
        # Add more features...
        
        return features
```

### Integrating the Custom Mapper

To use your custom mapper, you need to integrate it with the mapping engine:

```python
from migration_tool.core.mapping_engine import MappingEngine
from custom_mappers import MachineLearningSymbolMapper

class EnhancedMappingEngine(MappingEngine):
    """
    Enhanced mapping engine with ML-based symbol mapping.
    """
    
    def __init__(self, config_manager, logger=None, cache_manager=None):
        """Initialize the enhanced mapping engine."""
        super().__init__(config_manager, logger, cache_manager)
        
        # Replace the default symbol mapper with our custom one
        config = config_manager.get_config()
        self.symbol_mapper = MachineLearningSymbolMapper(config.get('mapping', {}), logger)
```

### Using the Custom Mapper

To use the custom mapper in your application:

```python
from migration_tool.core.mapping_engine import get_mapping_engine
from custom_mappers import EnhancedMappingEngine

# Register the enhanced mapping engine
get_mapping_engine.register("ml_enhanced")(EnhancedMappingEngine)

# Use the enhanced mapping engine
config_manager = ConfigManager("config.yaml")
mapping_engine = get_mapping_engine("ml_enhanced")(config_manager)

# Perform mapping
results = mapping_engine.map_components(components)
```

## Advanced ML-Based Mapping Capabilities

The Altium to KiCAD Database Migration Tool supports advanced machine learning techniques for component mapping. This section describes how to implement and use these capabilities.

### ML-Based Mapping Architecture

The ML-based mapping system consists of several components:

1. **Feature Extraction**: Converting component data into feature vectors
2. **Model Training**: Training ML models on labeled data
3. **Prediction**: Using trained models to predict mappings
4. **Confidence Scoring**: Assessing the reliability of predictions
5. **Fallback Mechanisms**: Handling cases where ML predictions are uncertain

### Implementing a Comprehensive ML Mapper

Here's an example of a more comprehensive ML-based mapper:

```python
from migration_tool.core.mapping_engine import SymbolMapper
from migration_tool.utils.logging_utils import setup_logger
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

class AdvancedMLSymbolMapper(SymbolMapper):
    """
    Advanced symbol mapper using multiple ML techniques.
    """
    
    def __init__(self, config, logger=None):
        """Initialize the advanced ML mapper."""
        super().__init__(config, logger)
        self.logger = logger or setup_logger(__name__)
        
        # Initialize models
        self.text_vectorizer = None
        self.classifier = None
        self.fallback_threshold = config.get('ml_fallback_threshold', 0.6)
        
        # Load models
        self._load_models()
        
    def _load_models(self):
        """Load ML models and vectorizers."""
        try:
            import joblib
            
            # Load text vectorizer
            vectorizer_path = self.config.get('ml_vectorizer_path', 'models/tfidf_vectorizer.pkl')
            self.logger.info(f"Loading text vectorizer from {vectorizer_path}")
            self.text_vectorizer = joblib.load(vectorizer_path)
            
            # Load classifier
            model_path = self.config.get('ml_model_path', 'models/symbol_classifier.pkl')
            self.logger.info(f"Loading classifier from {model_path}")
            self.classifier = joblib.load(model_path)
            
            self.logger.info("ML models loaded successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to load ML models: {str(e)}. Falling back to rule-based mapping.")
            self.text_vectorizer = None
            self.classifier = None
    
    def map_symbol(self, component):
        """Map an Altium symbol to a KiCAD symbol using ML techniques."""
        # If models failed to load, fall back to parent implementation
        if self.text_vectorizer is None or self.classifier is None:
            return super().map_symbol(component)
        
        try:
            # Extract text features
            text_features = self._extract_text_features(component)
            
            # Extract numerical features
            numerical_features = self._extract_numerical_features(component)
            
            # Combine features
            combined_features = self._combine_features(text_features, numerical_features)
            
            # Get predictions and probabilities
            predictions = self.classifier.predict([combined_features])[0]
            probabilities = self.classifier.predict_proba([combined_features])[0]
            
            # Get the highest probability and corresponding symbol
            max_prob_idx = np.argmax(probabilities)
            confidence = probabilities[max_prob_idx]
            symbol_name = self.classifier.classes_[max_prob_idx]
            
            self.logger.debug(f"ML mapped '{component.get('LibRef')}' to '{symbol_name}' with confidence {confidence:.2f}")
            
            # If confidence is below threshold, fall back to rule-based mapping
            if confidence < self.fallback_threshold:
                self.logger.debug(f"Confidence {confidence:.2f} below threshold {self.fallback_threshold}, falling back to rule-based mapping")
                return super().map_symbol(component)
            
            return symbol_name, float(confidence)
            
        except Exception as e:
            self.logger.error(f"ML mapping failed: {str(e)}. Falling back to rule-based mapping.")
            return super().map_symbol(component)
    
    def _extract_text_features(self, component):
        """Extract text features from component."""
        # Combine relevant text fields
        text = " ".join([
            component.get('LibRef', ''),
            component.get('Description', ''),
            component.get('Comment', ''),
            component.get('Value', '')
        ])
        
        # Transform text using vectorizer
        if text.strip():
            return self.text_vectorizer.transform([text]).toarray()[0]
        else:
            return np.zeros(self.text_vectorizer.get_feature_names_out().shape[0])
    
    def _extract_numerical_features(self, component):
        """Extract numerical features from component."""
        features = []
        
        # Component type indicators (one-hot encoding)
        features.append(1 if 'resistor' in component.get('Description', '').lower() else 0)
        features.append(1 if 'capacitor' in component.get('Description', '').lower() else 0)
        features.append(1 if 'inductor' in component.get('Description', '').lower() else 0)
        features.append(1 if 'diode' in component.get('Description', '').lower() else 0)
        features.append(1 if 'transistor' in component.get('Description', '').lower() else 0)
        features.append(1 if 'ic' in component.get('Description', '').lower() else 0)
        
        # Pin count (if available)
        pin_count = 0
        try:
            pin_count_str = component.get('PinCount', '0')
            pin_count = int(pin_count_str)
        except (ValueError, TypeError):
            pass
        features.append(pin_count)
        
        return np.array(features)
    
    def _combine_features(self, text_features, numerical_features):
        """Combine text and numerical features."""
        return np.concatenate([text_features, numerical_features])
```

### Training ML Models for Component Mapping

To train ML models for component mapping:

```python
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

def train_ml_models(training_data_path, output_dir):
    """
    Train ML models for component mapping.
    
    Args:
        training_data_path: Path to training data CSV
        output_dir: Directory to save models
    """
    # Load training data
    data = pd.read_csv(training_data_path)
    
    # Prepare text data
    text_data = data['Description'] + ' ' + data['LibRef'] + ' ' + data['Comment']
    
    # Create and fit vectorizer
    vectorizer = TfidfVectorizer(max_features=1000)
    text_features = vectorizer.fit_transform(text_data)
    
    # Prepare numerical features
    numerical_features = np.column_stack([
        data['PinCount'].fillna(0),
        # Add more numerical features...
    ])
    
    # Combine features
    features = np.hstack([
        text_features.toarray(),
        numerical_features
    ])
    
    # Prepare target
    target = data['KiCadSymbol']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42
    )
    
    # Train classifier
    classifier = RandomForestClassifier(n_estimators=100, random_state=42)
    classifier.fit(X_train, y_train)
    
    # Evaluate
    y_pred = classifier.predict(X_test)
    print(classification_report(y_test, y_pred))
    
    # Save models
    joblib.dump(vectorizer, f"{output_dir}/tfidf_vectorizer.pkl")
    joblib.dump(classifier, f"{output_dir}/symbol_classifier.pkl")
    
    print(f"Models saved to {output_dir}")
```

### Benchmarking ML Mapping Performance

The tool includes benchmarking capabilities to evaluate ML mapping performance:

```python
def benchmark_ml_mapper(test_data_path, models_dir):
    """
    Benchmark ML mapper performance.
    
    Args:
        test_data_path: Path to test data
        models_dir: Directory containing ML models
    """
    # Load test data
    test_data = pd.read_csv(test_data_path)
    
    # Create mappers
    rule_based_mapper = SymbolMapper(config={})
    ml_mapper = AdvancedMLSymbolMapper(config={
        'ml_vectorizer_path': f"{models_dir}/tfidf_vectorizer.pkl",
        'ml_model_path': f"{models_dir}/symbol_classifier.pkl",
        'ml_fallback_threshold': 0.6
    })
    
    # Benchmark results
    results = {
        'rule_based': {'correct': 0, 'total': 0, 'time': 0},
        'ml_based': {'correct': 0, 'total': 0, 'time': 0}
    }
    
    # Run benchmark
    for _, row in test_data.iterrows():
        component = row.to_dict()
        expected_symbol = component['KiCadSymbol']
        
        # Test rule-based mapper
        start_time = time.time()
        rule_symbol, rule_confidence = rule_based_mapper.map_symbol(component)
        rule_time = time.time() - start_time
        
        results['rule_based']['total'] += 1
        results['rule_based']['time'] += rule_time
        if rule_symbol == expected_symbol:
            results['rule_based']['correct'] += 1
        
        # Test ML-based mapper
        start_time = time.time()
        ml_symbol, ml_confidence = ml_mapper.map_symbol(component)
        ml_time = time.time() - start_time
        
        results['ml_based']['total'] += 1
        results['ml_based']['time'] += ml_time
        if ml_symbol == expected_symbol:
            results['ml_based']['correct'] += 1
    
    # Calculate metrics
    for mapper_type in results:
        results[mapper_type]['accuracy'] = results[mapper_type]['correct'] / results[mapper_type]['total']
        results[mapper_type]['avg_time'] = results[mapper_type]['time'] / results[mapper_type]['total']
    
    return results
```

### Deployment Automation

To automate the deployment of ML models:

```python
def deploy_ml_models(models_dir, target_dir):
    """
    Deploy ML models to target directory.
    
    Args:
        models_dir: Source directory containing trained models
        target_dir: Target directory for deployment
    """
    import shutil
    import os
    
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    # Copy model files
    for model_file in ['tfidf_vectorizer.pkl', 'symbol_classifier.pkl']:
        source_path = os.path.join(models_dir, model_file)
        target_path = os.path.join(target_dir, model_file)
        
        if os.path.exists(source_path):
            shutil.copy2(source_path, target_path)
            print(f"Deployed {model_file} to {target_path}")
        else:
            print(f"Warning: {source_path} not found")
```

### Implementation Guide

To implement ML-based mapping in your project:

1. **Collect Training Data**: Gather a dataset of Altium components with known KiCAD mappings
2. **Prepare Features**: Extract relevant features from component data
3. **Train Models**: Train ML models using the provided functions
4. **Deploy Models**: Deploy the trained models to your project
5. **Implement Mapper**: Create a custom mapper class that uses the models
6. **Integrate with Engine**: Integrate your mapper with the mapping engine
7. **Monitor Performance**: Track mapping accuracy and performance metrics

### Architecture Overview

The ML-based mapping architecture follows these principles:

1. **Modularity**: ML components are modular and can be replaced or upgraded
2. **Fallback Mechanisms**: ML mappers fall back to rule-based mapping when confidence is low
3. **Feature Engineering**: Comprehensive feature extraction for optimal performance
4. **Model Versioning**: Support for versioning and updating ML models
5. **Performance Monitoring**: Tracking of mapping accuracy and performance

By implementing these advanced ML-based mapping capabilities, you can significantly improve the accuracy and reliability of component mapping in the Altium to KiCAD Database Migration Tool.

Users can then use your custom mapper by specifying it in their configuration:

```yaml
mapping:
  symbol_mapper: "ml"  # Use ML-based symbol mapper
  ml_model_path: "models/custom_model.pkl"
  min_confidence: 0.6
```

## Creating Custom Output Generators

### Implementing a New Output Generator

To create a new output format, implement a custom output generator:

```python
from migration_tool.core.kicad_generator import OutputGenerator
from migration_tool.utils.logging_utils import setup_logger

@OutputGenerator.register("json")
class JSONOutputGenerator(OutputGenerator):
    """
    Generator for JSON output format.
    """
    
    def __init__(self, config, logger=None):
        """
        Initialize the generator.
        
        Args:
            config: Output configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or setup_logger(__name__)
    
    def generate(self, components, output_path):
        """
        Generate JSON output.
        
        Args:
            components: List of mapped components
            output_path: Output directory path
            
        Returns:
            Path to the generated file
        """
        import json
        import os
        
        self.logger.info(f"Generating JSON output at {output_path}")
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert components to serializable format
        serializable_components = []
        for component in components:
            serializable_component = {
                'libref': component.get('LibRef', ''),
                'description': component.get('Description', ''),
                'symbol': component.get('Symbol', {}).get('name', ''),
                'footprint': component.get('Footprint', {}).get('name', ''),
                'fields': component.get('Fields', {}),
                'metadata': {
                    'confidence': component.get('Confidence', 0),
                    'mapping_method': component.get('MappingMethod', '')
                }
            }
            serializable_components.append(serializable_component)
        
        # Write to JSON file
        with open(output_path, 'w') as f:
            json.dump({
                'components': serializable_components,
                'metadata': {
                    'component_count': len(components),
                    'generated_at': datetime.datetime.now().isoformat(),
                    'generator_version': self.config.get('version', '1.0.0')
                }
            }, f, indent=2)
        
        self.logger.info(f"JSON output generated successfully: {output_path}")
        return output_path
```

### Registering the Generator

The `@OutputGenerator.register("json")` decorator registers your generator with the system. Users can then use your generator by specifying the output format:

```yaml
output:
  format: json
  pretty_print: true
```

## Developing Plugins

### Plugin System Architecture

The tool includes a plugin system that allows for extending functionality without modifying the core code:

```
migration_tool/
├── plugins/
│   ├── __init__.py
│   ├── plugin_manager.py
│   └── base_plugin.py
```

### Creating a Plugin

To create a plugin, inherit from the `BasePlugin` class:

```python
from migration_tool.plugins.base_plugin import BasePlugin

class StatisticsPlugin(BasePlugin):
    """
    Plugin that generates statistics about the migration.
    """
    
    # Plugin metadata
    name = "statistics"
    version = "1.0.0"
    description = "Generates statistics about the migration process"
    author = "Your Name"
    
    def __init__(self, config=None):
        """Initialize the plugin."""
        super().__init__(config)
        self.stats = {
            'component_count': 0,
            'mapped_count': 0,
            'high_confidence_count': 0,
            'low_confidence_count': 0,
            'symbol_types': {},
            'footprint_types': {}
        }
    
    def on_migration_start(self, context):
        """Called when migration starts."""
        self.logger.info("Statistics plugin activated")
    
    def on_component_mapped(self, component, context):
        """Called when a component is mapped."""
        self.stats['component_count'] += 1
        
        if component.get('Symbol') and component.get('Footprint'):
            self.stats['mapped_count'] += 1
            
        confidence = component.get('Confidence', 0)
        if confidence >= 0.8:
            self.stats['high_confidence_count'] += 1
        else:
            self.stats['low_confidence_count'] += 1
            
        # Track symbol types
        symbol = component.get('Symbol', {}).get('name', 'Unknown')
        self.stats['symbol_types'][symbol] = self.stats['symbol_types'].get(symbol, 0) + 1
        
        # Track footprint types
        footprint = component.get('Footprint', {}).get('name', 'Unknown')
        self.stats['footprint_types'][footprint] = self.stats['footprint_types'].get(footprint, 0) + 1
    
    def on_migration_complete(self, result, context):
        """Called when migration completes."""
        import json
        import os
        
        # Calculate percentages
        if self.stats['component_count'] > 0:
            self.stats['mapped_percentage'] = (self.stats['mapped_count'] / self.stats['component_count']) * 100
            self.stats['high_confidence_percentage'] = (self.stats['high_confidence_count'] / self.stats['component_count']) * 100
        
        # Generate report
        output_dir = result.get('output_path', '.')
        stats_path = os.path.join(output_dir, 'migration_statistics.json')
        
        with open(stats_path, 'w') as f:
            json.dump(self.stats, f, indent=2)
            
        self.logger.info(f"Migration statistics saved to {stats_path}")
        
        # Add to result
        result['statistics'] = self.stats
        result['statistics_path'] = stats_path
```

### Registering a Plugin

Plugins are registered in the plugin registry:

```python
# migration_tool/plugins/__init__.py
from migration_tool.plugins.plugin_manager import register_plugin
from custom_plugins.statistics_plugin import StatisticsPlugin

# Register plugins
register_plugin(StatisticsPlugin)
```

### Using Plugins

Users can enable plugins in their configuration:

```yaml
plugins:
  - name: statistics
    enabled: true
    config:
      detailed: true
      include_charts: true
```

## Creating Custom User Interfaces

### Command Line Interface Extension

To extend the command line interface with new commands:

```python
from migration_tool.cli import cli_parser

def add_custom_commands(parser):
    """Add custom commands to the CLI parser."""
    # Add a new command group
    custom_group = parser.add_argument_group('Custom Commands')
    
    # Add arguments
    custom_group.add_argument(
        '--generate-statistics',
        action='store_true',
        help='Generate detailed statistics about the migration'
    )
    
    custom_group.add_argument(
        '--export-format',
        choices=['json', 'csv', 'xml'],
        help='Export format for statistics'
    )

# Register the extension
cli_parser.register_extension(add_custom_commands)
```

### Graphical Interface Extension

To extend the graphical interface with new features:

```python
from migration_tool.gui import register_gui_extension
import tkinter as tk
from tkinter import ttk

class StatisticsTab:
    """Custom tab for statistics in the GUI."""
    
    def __init__(self, parent, api):
        """Initialize the tab."""
        self.parent = parent
        self.api = api
        self.frame = ttk.Frame(parent)
        
        # Create UI elements
        self.create_widgets()
    
    def create_widgets(self):
        """Create the UI widgets."""
        # Title
        ttk.Label(
            self.frame, 
            text="Migration Statistics", 
            font=("Helvetica", 16)
        ).pack(pady=10)
        
        # Statistics display area
        self.stats_text = tk.Text(self.frame, height=20, width=60)
        self.stats_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Refresh button
        ttk.Button(
            self.frame, 
            text="Refresh Statistics",
            command=self.refresh_statistics
        ).pack(pady=10)
    
    def refresh_statistics(self):
        """Refresh the statistics display."""
        # Clear current content
        self.stats_text.delete(1.0, tk.END)
        
        # Get statistics from the API
        try:
            stats = self.api.get_statistics()
            
            # Display statistics
            self.stats_text.insert(tk.END, f"Total Components: {stats['component_count']}\n")
            self.stats_text.insert(tk.END, f"Mapped Components: {stats['mapped_count']} ({stats.get('mapped_percentage', 0):.1f}%)\n")
            self.stats_text.insert(tk.END, f"High Confidence: {stats['high_confidence_count']} ({stats.get('high_confidence_percentage', 0):.1f}%)\n")
            self.stats_text.insert(tk.END, f"Low Confidence: {stats['low_confidence_count']}\n\n")
            
            # Symbol types
            self.stats_text.insert(tk.END, "Top Symbol Types:\n")
            for symbol, count in sorted(stats['symbol_types'].items(), key=lambda x: x[1], reverse=True)[:10]:
                self.stats_text.insert(tk.END, f"  {symbol}: {count}\n")
                
            # Footprint types
            self.stats_text.insert(tk.END, "\nTop Footprint Types:\n")
            for footprint, count in sorted(stats['footprint_types'].items(), key=lambda x: x[1], reverse=True)[:10]:
                self.stats_text.insert(tk.END, f"  {footprint}: {count}\n")
                
        except Exception as e:
            self.stats_text.insert(tk.END, f"Error retrieving statistics: {str(e)}")
    
    def get_frame(self):
        """Get the frame for this tab."""
        return self.frame
    
    def on_tab_selected(self):
        """Called when this tab is selected."""
        self.refresh_statistics()

# Register the extension
def register_statistics_tab(gui):
    """Register the statistics tab with the GUI."""
    gui.add_tab("Statistics", StatisticsTab)

register_gui_extension(register_statistics_tab)
```

## Best Practices for Extensions

### 1. Follow the Existing Architecture

- Study the existing code to understand the architecture
- Follow established patterns and conventions
- Maintain separation of concerns

### 2. Write Comprehensive Tests

- Write unit tests for all new functionality
- Include integration tests for component interactions
- Test edge cases and error conditions

### 3. Document Your Extensions

- Add docstrings to all classes and methods
- Update user documentation for user-facing features
- Create developer documentation for extension points

### 4. Handle Errors Gracefully

- Use appropriate exception types
- Provide helpful error messages
- Implement fallback mechanisms where appropriate

### 5. Consider Performance

- Profile your code to identify bottlenecks
- Implement caching for expensive operations
- Use efficient algorithms and data structures

### 6. Maintain Backward Compatibility

- Avoid breaking changes to existing APIs
- Provide migration paths for configuration changes
- Support deprecated features for a transition period

## Packaging and Distribution

### Creating a Distribution Package

To package your extension for distribution:

1. **Create a Package Structure**:
   ```
   altium2kicad_extension/
   ├── __init__.py
   ├── setup.py
   ├── README.md
   └── altium2kicad_extension/
       ├── __init__.py
       ├── custom_mapper.py
       ├── custom_generator.py
       └── plugins/
           ├── __init__.py
           └── statistics_plugin.py
   ```

2. **Create setup.py**:
   ```python
   from setuptools import setup, find_packages

   setup(
       name="altium2kicad-extension",
       version="1.0.0",
       description="Extension for Altium to KiCAD Migration Tool",
       author="Your Name",
       author_email="your.email@example.com",
       packages=find_packages(),
       install_requires=[
           "altium2kicad-db>=1.0.0",
           "scikit-learn>=0.24.0",  # For ML mapper
           "joblib>=1.0.0"
       ],
       entry_points={
           "altium2kicad.plugins": [
               "statistics=altium2kicad_extension.plugins.statistics_plugin:StatisticsPlugin"
           ],
           "altium2kicad.mappers": [
               "ml=altium2kicad_extension.custom_mapper:MachineLearningSymbolMapper"
           ],
           "altium2kicad.generators": [
               "json=altium2kicad_extension.custom_generator:JSONOutputGenerator"
           ]
       }
   )
   ```

3. **Publish to PyPI**:
   ```bash
   python setup.py sdist bdist_wheel
   twine upload dist/*
   ```

### Installing Extensions

Users can install your extension with pip:

```bash
pip install altium2kicad-extension
```

## Conclusion

By leveraging these extension points, you can customize and enhance the Altium to KiCAD Database Migration Tool to meet specific requirements. Whether you're adding support for a new database type, implementing advanced mapping algorithms, or creating custom output formats, the modular architecture makes it straightforward to extend the tool's functionality.

For more information, refer to the [API Reference](api_reference.md) and [Architecture Overview](architecture.md) documents.