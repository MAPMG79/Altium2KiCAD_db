# Enterprise Deployment Guide

This guide provides detailed instructions for deploying the Altium to KiCAD Database Migration Tool in an enterprise environment. It covers installation, configuration, integration with existing systems, and best practices for managing large-scale migrations.

## Enterprise Use Cases

The Altium to KiCAD Database Migration Tool can be deployed in enterprise environments for:

1. **Company-wide EDA Migration**: Transitioning an entire organization from Altium to KiCAD
2. **Library Standardization**: Creating standardized component libraries across multiple teams
3. **Continuous Integration**: Automating library updates as part of CI/CD pipelines
4. **Multi-site Deployment**: Supporting component library migration across multiple locations
5. **Centralized Component Management**: Integrating with PLM/PDM systems for component management

## System Requirements

For enterprise deployments, we recommend:

- **Server Hardware**:
  - CPU: 8+ cores
  - RAM: 16+ GB
  - Storage: 100+ GB SSD
  - Network: 1 Gbps Ethernet

- **Operating System**:
  - Linux (Ubuntu 20.04 LTS or newer, RHEL/CentOS 8+)
  - Windows Server 2019 or newer
  - macOS 11 (Big Sur) or newer

- **Database Support**:
  - Microsoft SQL Server
  - MySQL/MariaDB
  - PostgreSQL
  - Oracle Database
  - SQLite (for smaller deployments)

- **Additional Requirements**:
  - Python 3.8 or newer
  - Docker (optional, for containerized deployment)
  - Web server (optional, for web interface)

## Deployment Options

### Option 1: Centralized Server Deployment

This option involves deploying the tool on a central server that all users can access.

#### Step 1: Server Setup

1. **Prepare the server**:
   ```bash
   # Update the system
   sudo apt update && sudo apt upgrade -y
   
   # Install dependencies
   sudo apt install -y python3 python3-pip python3-venv git unixodbc-dev
   ```

2. **Create a dedicated user**:
   ```bash
   sudo useradd -m altium2kicad
   sudo passwd altium2kicad
   ```

3. **Set up the application directory**:
   ```bash
   sudo mkdir -p /opt/altium2kicad
   sudo chown altium2kicad:altium2kicad /opt/altium2kicad
   ```

#### Step 2: Install the Tool

1. **Switch to the application user**:
   ```bash
   sudo su - altium2kicad
   ```

2. **Create a virtual environment**:
   ```bash
   cd /opt/altium2kicad
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the package**:
   ```bash
   pip install altium2kicad-db
   
   # Or install from source
   git clone https://github.com/yourusername/Altium2KiCAD_db.git
   cd Altium2KiCAD_db
   pip install -e .
   ```

4. **Install database drivers**:
   ```bash
   # For Microsoft SQL Server
   pip install pyodbc
   
   # For MySQL/MariaDB
   pip install mysqlclient
   
   # For PostgreSQL
   pip install psycopg2-binary
   
   # For Oracle
   pip install cx_Oracle
   ```

#### Step 3: Configure the Tool

1. **Create a configuration directory**:
   ```bash
   mkdir -p /opt/altium2kicad/config
   ```

2. **Create a base configuration file**:
   ```bash
   cat > /opt/altium2kicad/config/enterprise_config.yaml << 'EOF'
   # Enterprise configuration
   
   # Global settings
   global:
     output:
       directory: /opt/altium2kicad/output/
       format: sqlite
       create_report: true
     
     mapping:
       confidence_threshold: 0.7
       use_custom_rules: true
       custom_rules_path: /opt/altium2kicad/config/mapping_rules/
     
     validation:
       validate_symbols: true
       validate_footprints: true
       kicad_symbol_lib_path: /opt/altium2kicad/kicad_libs/symbols/
       kicad_footprint_lib_path: /opt/altium2kicad/kicad_libs/footprints/
     
     performance:
       parallel_processing: true
       max_workers: 8
       batch_size: 500
       cache_results: true
       cache_path: /opt/altium2kicad/cache/
     
     logging:
       log_level: INFO
       log_file: /opt/altium2kicad/logs/migration.log
       log_format: detailed
   
   # Security settings
   security:
     use_environment_vars: true
     mask_sensitive_data: true
   EOF
   ```

3. **Create directory structure**:
   ```bash
   mkdir -p /opt/altium2kicad/{output,logs,cache,kicad_libs/symbols,kicad_libs/footprints,config/mapping_rules}
   ```

4. **Set up environment variables for database credentials**:
   ```bash
   cat > /opt/altium2kicad/.env << 'EOF'
   DB_USERNAME=your_username
   DB_PASSWORD=your_password
   DB_SERVER=your_server
   EOF
   
   chmod 600 /opt/altium2kicad/.env
   ```

#### Step 4: Create a Service

1. **Create a systemd service file**:
   ```bash
   sudo cat > /etc/systemd/system/altium2kicad.service << 'EOF'
   [Unit]
   Description=Altium to KiCAD Migration Service
   After=network.target
   
   [Service]
   User=altium2kicad
   Group=altium2kicad
   WorkingDirectory=/opt/altium2kicad
   EnvironmentFile=/opt/altium2kicad/.env
   ExecStart=/opt/altium2kicad/venv/bin/python -m migration_tool.server --config /opt/altium2kicad/config/enterprise_config.yaml
   Restart=on-failure
   
   [Install]
   WantedBy=multi-user.target
   EOF
   ```

2. **Enable and start the service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable altium2kicad
   sudo systemctl start altium2kicad
   ```

3. **Check service status**:
   ```bash
   sudo systemctl status altium2kicad
   ```

### Option 2: Docker Deployment

For containerized deployment, use Docker:

#### Step 1: Create a Dockerfile

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    unixodbc-dev \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Create necessary directories
RUN mkdir -p output logs cache

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port for web interface
EXPOSE 8080

# Command to run the application
CMD ["python", "-m", "migration_tool.server", "--config", "config/enterprise_config.yaml"]
```

#### Step 2: Create Docker Compose File

```yaml
version: '3'

services:
  altium2kicad:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./config:/app/config
      - ./output:/app/output
      - ./logs:/app/logs
      - ./cache:/app/cache
      - ./kicad_libs:/app/kicad_libs
    environment:
      - DB_USERNAME=${DB_USERNAME}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_SERVER=${DB_SERVER}
    restart: unless-stopped
```

#### Step 3: Deploy with Docker Compose

```bash
# Create .env file with credentials
cat > .env << 'EOF'
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_SERVER=your_server
EOF

# Build and start the container
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Option 3: Web Application Deployment

For a web-based interface accessible to multiple users:

#### Step 1: Set Up the Web Server

1. **Install additional dependencies**:
   ```bash
   pip install flask gunicorn
   ```

2. **Create a web application configuration**:
   ```bash
   cat > /opt/altium2kicad/config/web_config.py << 'EOF'
   import os
   
   # Flask configuration
   SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
   DEBUG = False
   
   # Application configuration
   CONFIG_PATH = '/opt/altium2kicad/config/enterprise_config.yaml'
   UPLOAD_FOLDER = '/opt/altium2kicad/uploads'
   ALLOWED_EXTENSIONS = {'DbLib', 'db', 'sqlite'}
   
   # Authentication
   ENABLE_AUTH = True
   LDAP_SERVER = os.environ.get('LDAP_SERVER', '')
   LDAP_BASE_DN = os.environ.get('LDAP_BASE_DN', '')
   EOF
   ```

3. **Set up NGINX as a reverse proxy**:
   ```bash
   sudo apt install -y nginx
   
   sudo cat > /etc/nginx/sites-available/altium2kicad << 'EOF'
   server {
       listen 80;
       server_name altium2kicad.yourdomain.com;
   
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   EOF
   
   sudo ln -s /etc/nginx/sites-available/altium2kicad /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

4. **Create a service for the web application**:
   ```bash
   sudo cat > /etc/systemd/system/altium2kicad-web.service << 'EOF'
   [Unit]
   Description=Altium to KiCAD Migration Web Service
   After=network.target
   
   [Service]
   User=altium2kicad
   Group=altium2kicad
   WorkingDirectory=/opt/altium2kicad
   EnvironmentFile=/opt/altium2kicad/.env
   ExecStart=/opt/altium2kicad/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 migration_tool.web:app
   Restart=on-failure
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   sudo systemctl daemon-reload
   sudo systemctl enable altium2kicad-web
   sudo systemctl start altium2kicad-web
   ```

## Integration with Enterprise Systems

### PLM/PDM Integration

To integrate with Product Lifecycle Management (PLM) or Product Data Management (PDM) systems:

#### Step 1: Create an Integration Configuration

```yaml
# plm_integration.yaml
integration:
  type: plm
  system: teamcenter  # or windchill, enovia, etc.
  connection:
    url: https://plm.yourdomain.com/api
    username: ${PLM_USERNAME}
    password: ${PLM_PASSWORD}
    timeout: 60
  
  mapping:
    part_number_field: "PartNumber"
    description_field: "Description"
    manufacturer_field: "Manufacturer"
    value_field: "Value"
  
  synchronization:
    direction: bidirectional  # or import_only, export_only
    schedule: daily  # or hourly, weekly, manual
    conflict_resolution: newer  # or plm_wins, kicad_wins, manual
```

#### Step 2: Create Integration Scripts

```python
# plm_connector.py
from migration_tool import MigrationAPI
import yaml
import os
import requests
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='plm_integration.log'
)
logger = logging.getLogger('plm_integration')

def load_config(config_path):
    """Load the integration configuration."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def connect_to_plm(config):
    """Connect to the PLM system."""
    conn_config = config['integration']['connection']
    
    # Replace environment variables
    username = os.environ.get(conn_config['username'].strip('${}'), conn_config['username'])
    password = os.environ.get(conn_config['password'].strip('${}'), conn_config['password'])
    
    # Connect to PLM
    logger.info(f"Connecting to PLM system: {conn_config['url']}")
    
    try:
        # Implementation depends on the specific PLM system
        # This is a placeholder for the actual connection code
        response = requests.post(
            f"{conn_config['url']}/login",
            json={
                'username': username,
                'password': password
            },
            timeout=conn_config.get('timeout', 30)
        )
        
        if response.status_code == 200:
            token = response.json().get('token')
            logger.info("Successfully connected to PLM system")
            return {'token': token, 'url': conn_config['url']}
        else:
            logger.error(f"Failed to connect to PLM: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error connecting to PLM: {str(e)}")
        return None

def get_components_from_plm(plm_connection, config):
    """Retrieve components from the PLM system."""
    # Implementation depends on the specific PLM system
    # This is a placeholder for the actual retrieval code
    pass

def synchronize_components(config_path):
    """Synchronize components between PLM and KiCAD."""
    config = load_config(config_path)
    plm_connection = connect_to_plm(config)
    
    if not plm_connection:
        logger.error("PLM connection failed, aborting synchronization")
        return False
    
    # Get components from PLM
    plm_components = get_components_from_plm(plm_connection, config)
    
    # Initialize migration API
    api = MigrationAPI()
    
    # Process components
    # Implementation depends on the specific requirements
    
    logger.info("Synchronization completed")
    return True

if __name__ == "__main__":
    synchronize_components("plm_integration.yaml")
```

### Version Control Integration

To integrate with version control systems like Git:

#### Step 1: Create a Git Repository for Libraries

```bash
# Initialize a Git repository for KiCAD libraries
mkdir -p kicad_libraries
cd kicad_libraries
git init

# Create initial structure
mkdir -p symbols footprints 3dmodels templates

# Create a README
cat > README.md << 'EOF'
# KiCAD Libraries

This repository contains KiCAD libraries migrated from Altium.

## Structure
- symbols/ - Symbol libraries
- footprints/ - Footprint libraries
- 3dmodels/ - 3D models
- templates/ - Project templates

## Usage
[Instructions for using these libraries in KiCAD]
EOF

# Initial commit
git add .
git commit -m "Initial repository structure"
```

#### Step 2: Create a Migration Script with Git Integration

```python
# git_integration.py
import os
import subprocess
import yaml
from migration_tool import MigrationAPI
from datetime import datetime

def run_command(command):
    """Run a shell command and return the output."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    stdout, stderr = process.communicate()
    return {
        'returncode': process.returncode,
        'stdout': stdout.decode('utf-8'),
        'stderr': stderr.decode('utf-8')
    }

def migrate_and_commit(config_path, repo_path):
    """Run migration and commit changes to Git."""
    # Load configuration
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Set output directory to repository path
    config['output']['directory'] = repo_path
    
    # Initialize API
    api = MigrationAPI()
    
    # Run migration
    print(f"Running migration with config: {config_path}")
    result = api.run_migration(config)
    
    if not result['success']:
        print(f"Migration failed: {result.get('error', 'Unknown error')}")
        return False
    
    # Change to repository directory
    os.chdir(repo_path)
    
    # Check Git status
    status = run_command("git status --porcelain")
    if status['returncode'] != 0:
        print(f"Git error: {status['stderr']}")
        return False
    
    if not status['stdout'].strip():
        print("No changes to commit")
        return True
    
    # Add changes
    add_result = run_command("git add .")
    if add_result['returncode'] != 0:
        print(f"Git add error: {add_result['stderr']}")
        return False
    
    # Create commit message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Library update {timestamp}\n\n"
    commit_message += f"Components processed: {result['component_count']}\n"
    commit_message += f"Successfully mapped: {result['success_count']}\n"
    
    # Commit changes
    commit_result = run_command(f'git commit -m "{commit_message}"')
    if commit_result['returncode'] != 0:
        print(f"Git commit error: {commit_result['stderr']}")
        return False
    
    print(f"Changes committed: {commit_result['stdout']}")
    return True

if __name__ == "__main__":
    migrate_and_commit("migration_config.yaml", "/path/to/kicad_libraries")
```

### CI/CD Integration

To integrate with CI/CD pipelines like Jenkins or GitLab CI:

#### Jenkins Pipeline Example

```groovy
// Jenkinsfile
pipeline {
    agent {
        docker {
            image 'python:3.9'
        }
    }
    
    environment {
        DB_CREDENTIALS = credentials('altium-db-credentials')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install altium2kicad-db'
                sh 'mkdir -p output'
            }
        }
        
        stage('Migrate') {
            steps {
                sh '''
                cat > migration_config.yaml << EOF
                input:
                  path: ${ALTIUM_DBLIB_PATH}
                  connection:
                    username: ${DB_CREDENTIALS_USR}
                    password: ${DB_CREDENTIALS_PSW}
                
                output:
                  directory: output/
                  library_name: ${LIBRARY_NAME}
                  format: sqlite
                  create_report: true
                
                mapping:
                  confidence_threshold: 0.7
                  use_custom_rules: true
                  custom_rules_path: mapping_rules.yaml
                
                validation:
                  validate_symbols: true
                  validate_footprints: true
                EOF
                
                altium2kicad --config migration_config.yaml
                '''
            }
        }
        
        stage('Test') {
            steps {
                sh 'altium2kicad --validate-output output/${LIBRARY_NAME}.sqlite'
            }
        }
        
        stage('Publish') {
            steps {
                archiveArtifacts artifacts: 'output/**/*', fingerprint: true
                publishHTML(
                    target: [
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'output',
                        reportFiles: '*_report.html',
                        reportName: 'Migration Report'
                    ]
                )
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
    }
}
```

#### GitLab CI Example

```yaml
# .gitlab-ci.yml
image: python:3.9

stages:
  - setup
  - migrate
  - test
  - publish

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.pip-cache"

cache:
  paths:
    - .pip-cache/

setup:
  stage: setup
  script:
    - pip install altium2kicad-db
    - mkdir -p output
  artifacts:
    paths:
      - venv/

migrate:
  stage: migrate
  script:
    - |
      cat > migration_config.yaml << EOF
      input:
        path: ${ALTIUM_DBLIB_PATH}
        connection:
          username: ${DB_USERNAME}
          password: ${DB_PASSWORD}
      
      output:
        directory: output/
        library_name: ${LIBRARY_NAME}
        format: sqlite
        create_report: true
      
      mapping:
        confidence_threshold: 0.7
        use_custom_rules: true
        custom_rules_path: mapping_rules.yaml
      
      validation:
        validate_symbols: true
        validate_footprints: true
      EOF
      
      altium2kicad --config migration_config.yaml
  artifacts:
    paths:
      - output/
    reports:
      html: output/*_report.html

test:
  stage: test
  script:
    - altium2kicad --validate-output output/${LIBRARY_NAME}.sqlite

publish:
  stage: publish
  script:
    - |
      if [ "${CI_COMMIT_BRANCH}" = "main" ]; then
        # Copy to shared location or deploy
        mkdir -p /shared/libraries/
        cp output/${LIBRARY_NAME}.sqlite /shared/libraries/
      fi
  only:
    - main
```

## Multi-Site Deployment

For organizations with multiple sites:

### Centralized Model

In this model, a central server handles all migrations, and sites access the central repository:

1. **Set up a central server** as described in Option 1 above
2. **Configure network access** to allow all sites to reach the central server
3. **Set up a shared repository** for the migrated libraries
4. **Create site-specific configurations** for each location

### Distributed Model

In this model, each site has its own migration server, but they share configurations and rules:

1. **Set up a migration server at each site** using Option 1 or Option 2
2. **Create a central repository** for configurations and mapping rules
3. **Set up synchronization** to keep configurations in sync
4. **Implement a federated library system** to share migrated libraries between sites

## Security Considerations

### Database Credentials

1. **Use environment variables** for sensitive information:
   ```yaml
   connection:
     username: ${DB_USERNAME}
     password: ${DB_PASSWORD}
   ```

2. **Implement credential rotation**:
   ```bash
   # Create a credential rotation script
   cat > /opt/altium2kicad/scripts/rotate_credentials.sh << 'EOF'
   #!/bin/bash
   
   # Generate new password
   NEW_PASSWORD=$(openssl rand -base64 12)
   
   # Update database password
   # Implementation depends on your database system
   
   # Update environment file
   sed -i "s/DB_PASSWORD=.*/DB_PASSWORD=$NEW_PASSWORD/" /opt/altium2kicad/.env
   
   # Restart service to apply new credentials
   systemctl restart altium2kicad
   EOF
   
   chmod +x /opt/altium2kicad/scripts/rotate_credentials.sh
   ```

3. **Use a secrets management system** like HashiCorp Vault or AWS Secrets Manager

### Access Control

1. **Implement LDAP/Active Directory authentication**:
   ```python
   def authenticate_user(username, password):
       """Authenticate user against LDAP."""
       import ldap
       
       ldap_server = os.environ.get('LDAP_SERVER')
       base_dn = os.environ.get('LDAP_BASE_DN')
       
       try:
           # Connect to LDAP server
           conn = ldap.initialize(ldap_server)
           conn.protocol_version = ldap.VERSION3
           conn.set_option(ldap.OPT_REFERRALS, 0)
           
           # Bind with user credentials
           user_dn = f"uid={username},{base_dn}"
           conn.simple_bind_s(user_dn, password)
           
           # Search for user groups
           result = conn.search_s(
               base_dn,
               ldap.SCOPE_SUBTREE,
               f"(&(uid={username})(objectClass=posixGroup))",
               ['cn']
           )
           
           # Extract groups
           groups = [g.decode('utf-8') for g in result[0][1]['cn']]
           
           return {
               'authenticated': True,
               'username': username,
               'groups': groups
           }
           
       except ldap.INVALID_CREDENTIALS:
           return {'authenticated': False, 'error': 'Invalid credentials'}
       except ldap.LDAPError as e:
           return {'authenticated': False, 'error': str(e)}
   ```

2. **Implement role-based access control**:
   ```python
   def check_permission(user, action, resource):
       """Check if user has permission to perform action on resource."""
       # Define role-based permissions
       permissions = {
           'admin': ['read', 'write', 'execute', 'configure'],
           'engineer': ['read', 'write', 'execute'],
           'viewer': ['read']
       }
       
       # Get user's role
       role = get_user_role(user)
       
       # Check if action is allowed for this role
       return action in permissions.get(role, [])
   ```

### Network Security

1. **Use HTTPS** for all web interfaces
2. **Implement IP restrictions** to limit access to trusted networks
3. **Set up a VPN** for remote access
4. **Configure firewalls** to restrict access to necessary ports only

## Monitoring and Maintenance

### Monitoring

1. **Set up logging to a centralized log management system**:
   ```yaml
   logging:
     log_level: INFO
     log_file: /var/log/altium2kicad/migration.log
     syslog: true
     syslog_facility: local0
     log_format: json
   ```

2. **Implement health checks**:
   ```bash
   # Create a health check script
   cat > /opt/altium2kicad/scripts/health_check.sh << 'EOF'
   #!/bin/bash
   
   # Check if service is running
   systemctl is-active --quiet altium2kicad
   SERVICE_STATUS=$?
   
   # Check if web interface is accessible
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health
   WEB_STATUS=$?
   
   # Check disk space
   DISK_SPACE=$(df -h /opt/altium2kicad | awk 'NR==2 {print $5}' | tr -d '%')
   
   # Report status
   if [ $SERVICE_STATUS -eq 0 ] && [ $WEB_STATUS -eq 200 ] && [ $DISK_SPACE -lt 90 ]; then
     echo "Status: Healthy"
     exit 0
   else
     echo "Status: Unhealthy"
     echo "Service status: $SERVICE_STATUS"
     echo "Web status: $WEB_STATUS"
     echo "Disk space used: $DISK_SPACE%"
     exit 1
   fi
   EOF
   
   chmod +x /opt/altium2kicad/scripts/health_check.sh
   ```

3. **Set up alerts**:
   ```bash
   # Create an alert script
   cat > /opt/altium2kicad/scripts/alert.sh << 'EOF'
   #!/bin/bash
   
   # Send email alert
   send_email() {
     local subject="$1"
     local message="$2"
     local recipient="$3"
     
     echo "$message" | mail -s "$subject" "$recipient"
   }
   
   # Send Slack alert
   send_slack() {
     local message="$1"
     local webhook_url="$2"
     
     curl -X POST -H 'Content-type: application/json' \
       --data "{\"text\":\"$message\"}" \
       "$webhook_url"
   }
   
   # Main alert function
   alert() {
     local level="$1"
     local message="$2"
     
     # Log the alert
     logger -p "local0.$level" "$message"
     
     # Send notifications based on level
     case "$level" in
       "critical")
         send_email "CRITICAL ALERT: Altium2KiCAD" "$message" "admin@example.com"
         send_slack "CRITICAL ALERT: $message" "$SLACK_WEBHOOK_URL"
         ;;
       "error")
         send_email "ERROR ALERT: Altium2KiCAD" "$message" "admin@example.com"
         ;;
       "warning")
         send_slack "WARNING: $message" "$SLACK_WEBHOOK_URL"
         ;;
     esac
   }
   
   # Usage
   alert "$1" "$2"
   EOF
   
   chmod +x /opt/altium2kicad/scripts/alert.sh
   ```

### Maintenance

1. **Set up automatic updates**:
   ```bash
   # Create an update script
   cat > /opt/altium2kicad/scripts/update.sh << 'EOF'
   #!/bin/bash
   
   # Activate virtual environment
   source /opt/altium2kicad/venv/bin/activate
   
   # Backup current configuration
   cp -r /opt/altium2kicad/config /opt/altium2kicad/config.bak.$(date +%Y%m%d)
   
   # Update the package
   pip install --upgrade altium2kicad-db
   
   # Restart the service
   systemctl restart altium2kicad
   
   # Verify service is running
   systemctl is-active --quiet