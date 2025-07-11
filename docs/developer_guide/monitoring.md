# Monitoring and Metrics

This document describes the monitoring and metrics system for the Altium to KiCAD Database Migration Tool, including Prometheus and Grafana integration for comprehensive performance monitoring.

## Overview

The monitoring system provides real-time insights into the performance and health of the migration tool. Key features include:

1. **Metrics Collection**: Capturing performance and operational metrics
2. **Prometheus Integration**: Exposing metrics for collection by Prometheus
3. **Grafana Dashboards**: Visualizing metrics with customizable dashboards
4. **Advanced Logging**: Structured logging for detailed troubleshooting

## Metrics Collection

The tool collects various metrics during migration operations:

- **Performance Metrics**: Processing time, memory usage, component throughput
- **Success Metrics**: Success rates, error counts, recovery attempts
- **Resource Metrics**: CPU usage, database connections, file I/O
- **Component Metrics**: Component counts by type, mapping confidence scores

### Metric Types

The system supports several metric types:

- **Counters**: Monotonically increasing values (e.g., total components processed)
- **Gauges**: Values that can increase or decrease (e.g., current memory usage)
- **Histograms**: Distribution of values (e.g., processing time distribution)
- **Summaries**: Similar to histograms but with calculated quantiles

## Prometheus Integration

### Setting Up Prometheus

The tool includes built-in support for Prometheus monitoring. To configure Prometheus:

1. Create a Prometheus configuration file:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'altium-kicad-migration'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
```

2. Start the Prometheus server:

```bash
prometheus --config.file=prometheus.yml
```

### Exposing Metrics

The migration tool exposes metrics via an HTTP endpoint:

```python
# Example of setting up the metrics endpoint
from prometheus_client import start_http_server, Counter, Gauge, Histogram

# Initialize metrics
components_processed = Counter('components_processed_total', 'Total components processed')
migration_duration = Histogram('migration_duration_seconds', 'Time spent on migration')
memory_usage = Gauge('memory_usage_bytes', 'Current memory usage')

# Start metrics server
start_http_server(8080)
```

### Available Metrics

The following metrics are available:

| Metric Name | Type | Description |
|-------------|------|-------------|
| `components_processed_total` | Counter | Total number of components processed |
| `migration_success_total` | Counter | Total number of successful migrations |
| `migration_errors_total` | Counter | Total number of migration errors |
| `migration_duration_seconds` | Histogram | Time spent on migration operations |
| `memory_usage_bytes` | Gauge | Current memory usage |
| `database_connections` | Gauge | Current number of database connections |
| `mapping_confidence` | Histogram | Distribution of mapping confidence scores |

### Creating Prometheus Configuration

The tool can automatically generate a Prometheus configuration file:

```python
def create_prometheus_config(self) -> str:
    """Create Prometheus monitoring configuration"""
    config = {
        'global': {
            'scrape_interval': '15s',
            'evaluation_interval': '15s'
        },
        'scrape_configs': [
            {
                'job_name': 'altium-kicad-migration',
                'static_configs': [
                    {'targets': ['localhost:8080']}
                ],
                'metrics_path': '/metrics',
                'scrape_interval': '30s'
            }
        ],
        'alerting': {
            'alertmanagers': [
                {
                    'static_configs': [
                        {'targets': ['localhost:9093']}
                    ]
                }
            ]
        }
    }
    
    config_path = self.project_root / "monitoring" / "prometheus.yml"
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    return str(config_path)
```

## Grafana Integration

### Setting Up Grafana

To visualize metrics with Grafana:

1. Install and start Grafana:

```bash
# Start Grafana server
docker run -d -p 3000:3000 grafana/grafana
```

2. Add Prometheus as a data source:
   - Open Grafana (http://localhost:3000)
   - Go to Configuration > Data Sources
   - Add Prometheus data source (URL: http://localhost:9090)

### Creating Dashboards

The tool can automatically generate a Grafana dashboard configuration:

```python
def create_grafana_dashboard(self) -> str:
    """Create Grafana dashboard configuration"""
    dashboard = {
        'dashboard': {
            'id': None,
            'title': 'Altium to KiCAD Migration Tool',
            'tags': ['migration', 'kicad', 'altium'],
            'timezone': 'browser',
            'panels': [
                {
                    'id': 1,
                    'title': 'Migration Success Rate',
                    'type': 'stat',
                    'targets': [
                        {
                            'expr': 'migration_success_total / migration_total * 100',
                            'legendFormat': 'Success Rate %'
                        }
                    ]
                },
                {
                    'id': 2,
                    'title': 'Migration Duration',
                    'type': 'graph',
                    'targets': [
                        {
                            'expr': 'migration_duration_seconds',
                            'legendFormat': 'Duration (seconds)'
                        }
                    ]
                },
                {
                    'id': 3,
                    'title': 'Components Processed',
                    'type': 'graph',
                    'targets': [
                        {
                            'expr': 'components_processed_total',
                            'legendFormat': 'Components'
                        }
                    ]
                },
                {
                    'id': 4,
                    'title': 'Error Rate',
                    'type': 'graph',
                    'targets': [
                        {
                            'expr': 'migration_errors_total',
                            'legendFormat': 'Errors'
                        }
                    ]
                }
            ],
            'time': {
                'from': 'now-1h',
                'to': 'now'
            },
            'refresh': '30s'
        }
    }
    
    dashboard_path = self.project_root / "monitoring" / "grafana_dashboard.json"
    dashboard_path.parent.mkdir(exist_ok=True)
    
    with open(dashboard_path, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    return str(dashboard_path)
```

### Dashboard Panels

The default dashboard includes the following panels:

1. **Migration Success Rate**: Percentage of successful migrations
2. **Migration Duration**: Time spent on migration operations
3. **Components Processed**: Total number of components processed
4. **Error Rate**: Number of errors over time

### Importing Dashboards

To import the generated dashboard:

1. Open Grafana (http://localhost:3000)
2. Go to Dashboards > Import
3. Upload the generated JSON file or paste its contents
4. Select the Prometheus data source
5. Click Import

## Advanced Logging Configuration

The tool includes a sophisticated logging system that integrates with the monitoring system:

```python
def create_logging_config(self) -> str:
    """Create production logging configuration"""
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'json': {
                'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
            }
        },
        'handlers': {
            'default': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'level': 'DEBUG',
                'formatter': 'json',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/var/log/migration_tool/app.log',
                'maxBytes': 10485760,
                'backupCount': 5
            },
            'error_file': {
                'level': 'ERROR',
                'formatter': 'json',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/var/log/migration_tool/error.log',
                'maxBytes': 10485760,
                'backupCount': 5
            }
        },
        'loggers': {
            '': {
                'handlers': ['default', 'file', 'error_file'],
                'level': 'DEBUG',
                'propagate': False
            }
        }
    }
    
    config_path = self.project_root / "config" / "logging_production.yaml"
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    return str(config_path)
```

### Log Formats

The logging system supports multiple formats:

- **Standard Format**: Human-readable log messages
- **JSON Format**: Structured logs for machine processing

### Log Levels

The system uses standard log levels:

- **DEBUG**: Detailed debugging information
- **INFO**: General operational information
- **WARNING**: Warning events that might require attention
- **ERROR**: Error events that might still allow the application to continue
- **CRITICAL**: Critical events that might cause the application to terminate

### Log Rotation

The logging configuration includes log rotation to manage log file size:

- **Maximum Size**: 10MB per log file
- **Backup Count**: 5 backup files

## Integration with Application Code

### Recording Metrics

To record metrics in your code:

```python
from migration_tool.monitoring import metrics

# Record a counter
metrics.components_processed.inc()

# Record a histogram
with metrics.migration_duration.time():
    # Perform migration operation
    result = migration_engine.migrate(data)

# Record a gauge
metrics.memory_usage.set(get_memory_usage())
```

### Structured Logging

To use structured logging:

```python
import logging
import json

logger = logging.getLogger(__name__)

# Log with structured data
logger.info(json.dumps({
    'event': 'migration_started',
    'database': 'example.db',
    'tables': 5,
    'components': 1000
}))
```

## Monitoring in Production

For production deployments, consider:

1. **Persistent Storage**: Configure Prometheus and Grafana with persistent storage
2. **Authentication**: Secure access to monitoring interfaces
3. **Alerting**: Configure alerts for critical metrics
4. **High Availability**: Deploy redundant monitoring infrastructure

### Docker Compose Setup

A Docker Compose configuration for production monitoring:

```yaml
version: '3'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: always

  grafana:
    image: grafana/grafana
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    restart: always
    depends_on:
      - prometheus

  alertmanager:
    image: prom/alertmanager
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    ports:
      - "9093:9093"
    restart: always

volumes:
  prometheus_data:
  grafana_data:
```

## Best Practices

1. **Collect Meaningful Metrics**: Focus on metrics that provide actionable insights
2. **Use Appropriate Metric Types**: Choose the right metric type for each measurement
3. **Set Up Alerts**: Configure alerts for critical thresholds
4. **Retain Historical Data**: Configure appropriate data retention periods
5. **Monitor Resource Usage**: Track CPU, memory, and disk usage
6. **Correlate Logs and Metrics**: Use consistent identifiers across logs and metrics
7. **Document Dashboards**: Add documentation to dashboard panels

## Conclusion

The monitoring and metrics system provides comprehensive visibility into the performance and health of the Altium to KiCAD Database Migration Tool. By leveraging Prometheus and Grafana, you can gain valuable insights into migration operations and quickly identify and resolve issues.