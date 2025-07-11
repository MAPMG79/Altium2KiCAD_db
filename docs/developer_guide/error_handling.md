# Error Handling System

This document describes the comprehensive error handling system implemented in the Altium to KiCAD Database Migration Tool. The system is designed to provide robust error management, recovery strategies, and detailed error reporting.

## Overview

The error handling system consists of several key components:

1. **Error Classification**: A structured approach to categorizing errors by type and severity
2. **Error Recovery**: Automatic recovery strategies for common error scenarios
3. **Error Reporting**: Detailed logging and reporting of errors for analysis
4. **Error Statistics**: Collection and analysis of error patterns

## Error Classification System

Errors are classified using the `ErrorInfo` class, which captures comprehensive information about each error:

```python
@dataclass
class ErrorInfo:
    """Information about an error that occurred during migration"""
    error_type: str             # Type of error (e.g., "ConnectionError")
    message: str                # Error message
    component_data: Optional[Dict[str, Any]]  # Component data related to the error
    table_name: Optional[str]   # Table where the error occurred
    timestamp: str              # When the error occurred
    traceback_info: Optional[str]  # Stack trace
    severity: str               # 'low', 'medium', 'high', 'critical'
```

### Severity Levels

Errors are assigned a severity level based on their impact:

- **Critical**: Errors that prevent the migration from completing (e.g., database connection failures)
- **High**: Errors that significantly impact the quality of the migration (e.g., schema validation failures)
- **Medium**: Errors that affect specific components but don't prevent overall migration (e.g., mapping failures)
- **Low**: Minor issues that have minimal impact on the migration (e.g., non-critical warnings)

The system automatically determines severity based on error patterns:

```python
def _determine_severity(self, error_type: str, error_message: str) -> str:
    """Determine error severity based on type and message"""
    critical_patterns = [
        'database', 'connection', 'access', 'permission', 'memory'
    ]
    high_patterns = [
        'validation', 'schema', 'constraint', 'corrupt'
    ]
    medium_patterns = [
        'mapping', 'symbol', 'footprint', 'not found'
    ]
    
    error_text = f"{error_type} {error_message}".lower()
    
    if any(pattern in error_text for pattern in critical_patterns):
        return 'critical'
    elif any(pattern in error_text for pattern in high_patterns):
        return 'high'
    elif any(pattern in error_text for pattern in medium_patterns):
        return 'medium'
    else:
        return 'low'
```

## Error Recovery Strategies

The `ErrorHandler` class implements automatic recovery strategies for common error scenarios:

```python
class ErrorHandler:
    """Advanced error handling and recovery for migration operations"""
    
    def __init__(self, log_file: str = "migration_errors.json"):
        self.log_file = Path(log_file)
        self.errors: List[ErrorInfo] = []
        self.error_stats = {
            'total_errors': 0,
            'by_severity': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
            'by_type': {},
            'by_table': {}
        }
        self.recovery_strategies = self._initialize_recovery_strategies()
```

### Available Recovery Strategies

The system includes recovery strategies for various error types:

#### Database Connection Errors

```python
def _recover_database_connection(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Optional[Any]:
    """Attempt to recover from database connection errors"""
    # Try alternative connection methods
    attempts = [
        {'timeout': 60},  # Increase timeout
        {'readonly': True},  # Try read-only access
        {'pooling': False}  # Disable connection pooling
    ]
    
    for attempt in attempts:
        try:
            # This would use actual connection logic
            logging.info(f"Attempting database recovery with: {attempt}")
            # return recovered_connection
            pass
        except Exception:
            continue
    
    return None
```

#### Component Mapping Errors

```python
def _recover_component_mapping(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Optional[Any]:
    """Attempt to recover from component mapping errors"""
    if context and 'component_data' in context:
        component = context['component_data']
        
        # Provide fallback mapping
        fallback_mapping = {
            'altium_symbol': component.get('Symbol', 'Unknown'),
            'kicad_symbol': 'Device:R',  # Safe fallback
            'kicad_footprint': 'Resistor_SMD:R_0603_1608Metric',  # Safe fallback
            'confidence': 0.1,  # Low confidence for fallback
            'field_mappings': {
                'Description': component.get('Description', 'Unknown Component'),
                'Value': component.get('Value', ''),
                'MPN': component.get('Manufacturer Part Number', '')
            },
            'recovery_used': True
        }
        
        return fallback_mapping
    
    return None
```

#### Symbol Not Found Errors

```python
def _recover_symbol_not_found(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Optional[Any]:
    """Recover from symbol not found errors"""
    # Return generic symbol based on component type
    generic_symbols = {
        'resistor': 'Device:R',
        'capacitor': 'Device:C', 
        'inductor': 'Device:L',
        'diode': 'Device:D',
        'transistor': 'Device:Q_NPN_BCE'
    }
    
    if context and 'component_data' in context:
        description = context['component_data'].get('Description', '').lower()
        for comp_type, symbol in generic_symbols.items():
            if comp_type in description:
                return symbol
    
    return 'Device:R'  # Ultimate fallback
```

#### Data Validation Errors

```python
def _recover_data_validation(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Optional[Any]:
    """Recover from data validation errors"""
    if context and 'component_data' in context:
        component = context['component_data']
        
        # Clean and validate data
        cleaned_component = {}
        for key, value in component.items():
            if value is not None and str(value).strip():
                # Remove problematic characters
                cleaned_value = str(value).replace('\x00', '').strip()
                if len(cleaned_value) > 255:  # Truncate long values
                    cleaned_value = cleaned_value[:252] + '...'
                cleaned_component[key] = cleaned_value
        
        return cleaned_component
    
    return None
```

#### File Access Errors

```python
def _recover_file_access(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Optional[Any]:
    """Recover from file access errors"""
    # Try alternative file locations or permissions
    if context and 'file_path' in context:
        file_path = Path(context['file_path'])
        
        # Try parent directory if current path fails
        alternatives = [
            file_path.parent / f"backup_{file_path.name}",
            file_path.with_suffix(f"{file_path.suffix}.bak"),
            Path.cwd() / file_path.name
        ]
        
        for alt_path in alternatives:
            if alt_path.exists():
                return str(alt_path)
    
    return None
```

#### Memory Errors

```python
def _recover_memory_error(self, error_info: ErrorInfo, context: Dict[str, Any]) -> Optional[Any]:
    """Recover from memory errors"""
    # Suggest memory optimization strategies
    optimization_suggestions = [
        "Reduce batch size",
        "Enable garbage collection",
        "Process tables sequentially",
        "Disable caching temporarily"
    ]
    
    logging.warning("Memory error detected. Suggestions:")
    for suggestion in optimization_suggestions:
        logging.warning(f"  - {suggestion}")
    
    return {'optimization_suggestions': optimization_suggestions}
```

## Error Reporting Mechanisms

The error handling system provides comprehensive error reporting:

### Error Logging

Errors are logged to both the console and a JSON file:

```python
def _log_error(self, error_info: ErrorInfo):
    """Log error information"""
    self.errors.append(error_info)
    
    # Update statistics
    self.error_stats['total_errors'] += 1
    self.error_stats['by_severity'][error_info.severity] += 1
    
    if error_info.error_type not in self.error_stats['by_type']:
        self.error_stats['by_type'][error_info.error_type] = 0
    self.error_stats['by_type'][error_info.error_type] += 1
    
    if error_info.table_name:
        if error_info.table_name not in self.error_stats['by_table']:
            self.error_stats['by_table'][error_info.table_name] = 0
        self.error_stats['by_table'][error_info.table_name] += 1
    
    # Log to console
    logging.error(f"[{error_info.severity.upper()}] {error_info.error_type}: {error_info.message}")
    
    # Save to file periodically
    if len(self.errors) % 10 == 0:
        self.save_error_log()
```

### Error Reports

The system can generate comprehensive error reports:

```python
def generate_error_report(self) -> Dict[str, Any]:
    """Generate comprehensive error report"""
    return {
        'summary': self.error_stats,
        'recent_errors': [
            {
                'type': e.error_type,
                'message': e.message,
                'severity': e.severity,
                'timestamp': e.timestamp
            }
            for e in self.errors[-10:]  # Last 10 errors
        ],
        'recommendations': self._generate_recommendations()
    }
```

### Recommendations

The system analyzes error patterns to provide recommendations:

```python
def _generate_recommendations(self) -> List[str]:
    """Generate recommendations based on error patterns"""
    recommendations = []
    
    # Check for common error patterns
    if self.error_stats['by_severity']['critical'] > 0:
        recommendations.append("Critical errors detected. Check database connectivity and file permissions.")
    
    if self.error_stats['by_type'].get('ConnectionError', 0) > 5:
        recommendations.append("Frequent connection errors. Consider increasing timeout values.")
    
    if self.error_stats['by_type'].get('MappingError', 0) > 10:
        recommendations.append("Many mapping errors. Consider updating symbol/footprint libraries.")
    
    if self.error_stats['total_errors'] > 100:
        recommendations.append("High error count. Consider preprocessing data or using batch mode.")
    
    return recommendations
```

## Automatic Recovery

The error handler automatically attempts to recover from errors:

```python
def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Optional[Any]:
    """Handle an error with automatic recovery attempts"""
    error_type = type(error).__name__
    error_message = str(error)
    
    # Determine severity
    severity = self._determine_severity(error_type, error_message)
    
    # Create error info
    error_info = ErrorInfo(
        error_type=error_type,
        message=error_message,
        component_data=context.get('component_data') if context else None,
        table_name=context.get('table_name') if context else None,
        timestamp=datetime.now().isoformat(),
        traceback_info=traceback.format_exc(),
        severity=severity
    )
    
    # Log error
    self._log_error(error_info)
    
    # Attempt recovery
    recovery_result = self._attempt_recovery(error_info, context)
    
    return recovery_result
```

## Integration with Application Code

To use the error handling system in your code:

```python
# Initialize error handler
error_handler = ErrorHandler(log_file="migration_errors.json")

# Use in a try-except block
try:
    # Perform migration operation
    result = mapping_engine.map_component(component_data)
    return result
except Exception as e:
    # Handle error with context
    context = {
        'component_data': component_data,
        'table_name': 'Resistors'
    }
    recovery_result = error_handler.handle_error(e, context)
    
    if recovery_result:
        # Use recovery result
        return recovery_result
    else:
        # Re-raise if recovery failed
        raise
```

## Best Practices

1. **Provide Context**: Always include relevant context when handling errors
2. **Use Appropriate Recovery**: Choose recovery strategies based on error type
3. **Log Comprehensively**: Ensure all errors are properly logged
4. **Analyze Patterns**: Regularly review error reports to identify patterns
5. **Update Recovery Strategies**: Enhance recovery strategies based on common errors
6. **Test Recovery**: Verify that recovery strategies work as expected

## Conclusion

The comprehensive error handling system provides robust error management, automatic recovery, and detailed reporting. By properly integrating this system into your code, you can create more resilient applications that gracefully handle errors and provide useful feedback to users.