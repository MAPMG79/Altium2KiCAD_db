# Integration Guide

This guide provides detailed instructions for integrating the Altium to KiCAD Database Migration Tool into your development workflows, CI/CD pipelines, and external applications. It covers API usage, automation strategies, and best practices for version control.

## API Integration

The Altium to KiCAD Database Migration Tool provides a comprehensive API that can be used to integrate the migration functionality into your own applications.

### Python API

The Python API provides direct access to the migration functionality:

```python
from altium2kicad import AltiumToKiCADMigrator

# Initialize the migrator
migrator = AltiumToKiCADMigrator()

# Configure the migration
config = {
    "input": "path/to/library.DbLib",
    "output": "output_directory",
    "library_name": "MyLibrary",
    "parallel_processing": True,
    "max_workers": 4
}

# Run the migration
result = migrator.migrate(config)

# Process the results
if result.success:
    print(f"Migration completed successfully. {result.component_count} components migrated.")
    print(f"Output files: {result.output_files}")
else:
    print(f"Migration failed: {result.error_message}")
    print(f"Error details: {result.error_details}")
```

### RESTful API

The tool also provides a RESTful API for integration with non-Python applications:

#### Starting the API Server

```bash
# Start the API server
altium2kicad-api --host 0.0.0.0 --port 5000 --api-key your_api_key
```

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/migrate` | POST | Start a migration job |
| `/api/v1/jobs/{job_id}` | GET | Get job status |
| `/api/v1/jobs` | GET | List all jobs |
| `/api/v1/config` | GET | Get default configuration |
| `/api/v1/health` | GET | Check API health |

#### Example API Requests

**Start a migration job:**

```bash
curl -X POST "http://localhost:5000/api/v1/migrate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "input": "path/to/library.DbLib",
    "output": "output_directory",
    "library_name": "MyLibrary",
    "parallel_processing": true,
    "max_workers": 4
  }'
```

**Check job status:**

```bash
curl -X GET "http://localhost:5000/api/v1/jobs/job_12345" \
  -H "X-API-Key: your_api_key"
```

### API Integration Examples

#### JavaScript/Node.js

```javascript
const axios = require('axios');

async function migrateLibrary() {
  try {
    // Start migration job
    const response = await axios.post('http://localhost:5000/api/v1/migrate', {
      input: 'path/to/library.DbLib',
      output: 'output_directory',
      library_name: 'MyLibrary',
      parallel_processing: true,
      max_workers: 4
    }, {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'your_api_key'
      }
    });
    
    const jobId = response.data.job_id;
    console.log(`Migration job started with ID: ${jobId}`);
    
    // Poll for job completion
    let jobComplete = false;
    while (!jobComplete) {
      await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
      
      const statusResponse = await axios.get(`http://localhost:5000/api/v1/jobs/${jobId}`, {
        headers: {
          'X-API-Key': 'your_api_key'
        }
      });
      
      const status = statusResponse.data.status;
      console.log(`Job status: ${status}`);
      
      if (status === 'completed' || status === 'failed') {
        jobComplete = true;
        console.log(`Job result: ${JSON.stringify(statusResponse.data.result)}`);
      }
    }
  } catch (error) {
    console.error('Error during migration:', error.message);
  }
}

migrateLibrary();
```

#### C#/.NET

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

class Altium2KiCADClient
{
    private readonly HttpClient _client;
    private readonly string _apiKey;
    private readonly string _baseUrl;
    
    public Altium2KiCADClient(string baseUrl, string apiKey)
    {
        _baseUrl = baseUrl;
        _apiKey = apiKey;
        _client = new HttpClient();
        _client.DefaultRequestHeaders.Add("X-API-Key", _apiKey);
    }
    
    public async Task<string> StartMigrationJob(string inputPath, string outputPath, string libraryName)
    {
        var requestData = new
        {
            input = inputPath,
            output = outputPath,
            library_name = libraryName,
            parallel_processing = true,
            max_workers = 4
        };
        
        var content = new StringContent(JsonConvert.SerializeObject(requestData), Encoding.UTF8, "application/json");
        var response = await _client.PostAsync($"{_baseUrl}/api/v1/migrate", content);
        
        response.EnsureSuccessStatusCode();
        var responseBody = await response.Content.ReadAsStringAsync();
        dynamic result = JsonConvert.DeserializeObject(responseBody);
        
        return result.job_id;
    }
    
    public async Task<dynamic> GetJobStatus(string jobId)
    {
        var response = await _client.GetAsync($"{_baseUrl}/api/v1/jobs/{jobId}");
        response.EnsureSuccessStatusCode();
        var responseBody = await response.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject(responseBody);
    }
    
    public async Task WaitForJobCompletion(string jobId, int pollingIntervalSeconds = 5)
    {
        bool jobComplete = false;
        while (!jobComplete)
        {
            await Task.Delay(pollingIntervalSeconds * 1000);
            
            var status = await GetJobStatus(jobId);
            Console.WriteLine($"Job status: {status.status}");
            
            if (status.status == "completed" || status.status == "failed")
            {
                jobComplete = true;
                Console.WriteLine($"Job result: {JsonConvert.SerializeObject(status.result)}");
            }
        }
    }
}

class Program
{
    static async Task Main(string[] args)
    {
        var client = new Altium2KiCADClient("http://localhost:5000", "your_api_key");
        
        try
        {
            string jobId = await client.StartMigrationJob(
                "path/to/library.DbLib",
                "output_directory",
                "MyLibrary"
            );
            
            Console.WriteLine($"Migration job started with ID: {jobId}");
            await client.WaitForJobCompletion(jobId);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error during migration: {ex.Message}");
        }
    }
}
```

#### Java

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import org.json.JSONObject;

public class Altium2KiCADClient {
    private final HttpClient httpClient;
    private final String baseUrl;
    private final String apiKey;
    
    public Altium2KiCADClient(String baseUrl, String apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
        this.httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();
    }
    
    public String startMigrationJob(String inputPath, String outputPath, String libraryName) throws Exception {
        JSONObject requestData = new JSONObject();
        requestData.put("input", inputPath);
        requestData.put("output", outputPath);
        requestData.put("library_name", libraryName);
        requestData.put("parallel_processing", true);
        requestData.put("max_workers", 4);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/api/v1/migrate"))
            .header("Content-Type", "application/json")
            .header("X-API-Key", apiKey)
            .POST(HttpRequest.BodyPublishers.ofString(requestData.toString()))
            .build();
            
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() != 200) {
            throw new RuntimeException("API call failed with status code: " + response.statusCode());
        }
        
        JSONObject responseJson = new JSONObject(response.body());
        return responseJson.getString("job_id");
    }
    
    public JSONObject getJobStatus(String jobId) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/api/v1/jobs/" + jobId))
            .header("X-API-Key", apiKey)
            .GET()
            .build();
            
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() != 200) {
            throw new RuntimeException("API call failed with status code: " + response.statusCode());
        }
        
        return new JSONObject(response.body());
    }
    
    public void waitForJobCompletion(String jobId, int pollingIntervalSeconds) throws Exception {
        boolean jobComplete = false;
        while (!jobComplete) {
            Thread.sleep(pollingIntervalSeconds * 1000);
            
            JSONObject status = getJobStatus(jobId);
            System.out.println("Job status: " + status.getString("status"));
            
            if (status.getString("status").equals("completed") || status.getString("status").equals("failed")) {
                jobComplete = true;
                System.out.println("Job result: " + status.getJSONObject("result").toString());
            }
        }
    }
    
    public static void main(String[] args) {
        try {
            Altium2KiCADClient client = new Altium2KiCADClient("http://localhost:5000", "your_api_key");
            
            String jobId = client.startMigrationJob(
                "path/to/library.DbLib",
                "output_directory",
                "MyLibrary"
            );
            
            System.out.println("Migration job started with ID: " + jobId);
            client.waitForJobCompletion(jobId, 5);
        } catch (Exception e) {
            System.err.println("Error during migration: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
```

## CI/CD Integration

### GitHub Actions

Integrate the migration tool into your GitHub Actions workflow:

```yaml
# .github/workflows/migrate-libraries.yml
name: Migrate Component Libraries

on:
  push:
    branches: [ main ]
    paths:
      - 'altium_libraries/**'
  pull_request:
    branches: [ main ]
    paths:
      - 'altium_libraries/**'
  workflow_dispatch:

jobs:
  migrate:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install altium2kicad
    
    - name: Run migration
      run: |
        altium2kicad --input altium_libraries/main_library.DbLib \
                     --output kicad_libraries \
                     --library-name MainLibrary \
                     --parallel-processing \
                     --max-workers 4 \
                     --generate-report
    
    - name: Upload KiCAD libraries
      uses: actions/upload-artifact@v2
      with:
        name: kicad-libraries
        path: kicad_libraries/
    
    - name: Upload migration report
      uses: actions/upload-artifact@v2
      with:
        name: migration-report
        path: migration_report.html
```

### GitLab CI/CD

Integrate the migration tool into your GitLab CI/CD pipeline:

```yaml
# .gitlab-ci.yml
stages:
  - migrate
  - deploy

migrate_libraries:
  stage: migrate
  image: python:3.9
  script:
    - pip install altium2kicad
    - altium2kicad --input altium_libraries/main_library.DbLib --output kicad_libraries --library-name MainLibrary --parallel-processing --max-workers 4 --generate-report
  artifacts:
    paths:
      - kicad_libraries/
      - migration_report.html
  only:
    changes:
      - altium_libraries/**
    refs:
      - main
      - merge_requests

deploy_libraries:
  stage: deploy
  image: alpine:latest
  script:
    - apk add --no-cache rsync openssh
    - mkdir -p ~/.ssh
    - echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
    - chmod 600 ~/.ssh/id_rsa
    - echo "$SSH_KNOWN_HOSTS" > ~/.ssh/known_hosts
    - rsync -avz --delete kicad_libraries/ user@server:/path/to/kicad/libraries/
  only:
    refs:
      - main
  dependencies:
    - migrate_libraries
```

### Jenkins Pipeline

Integrate the migration tool into your Jenkins pipeline:

```groovy
// Jenkinsfile
pipeline {
    agent {
        docker {
            image 'python:3.9'
        }
    }
    
    stages {
        stage('Install') {
            steps {
                sh 'pip install altium2kicad'
            }
        }
        
        stage('Migrate') {
            steps {
                sh '''
                altium2kicad --input altium_libraries/main_library.DbLib \
                             --output kicad_libraries \
                             --library-name MainLibrary \
                             --parallel-processing \
                             --max-workers 4 \
                             --generate-report
                '''
            }
        }
        
        stage('Archive') {
            steps {
                archiveArtifacts artifacts: 'kicad_libraries/**', fingerprint: true
                archiveArtifacts artifacts: 'migration_report.html', fingerprint: true
            }
        }
    }
    
    post {
        success {
            emailext (
                subject: "Migration Successful: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "The library migration completed successfully. See ${env.BUILD_URL} for details.",
                to: 'team@example.com'
            )
        }
        failure {
            emailext (
                subject: "Migration Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "The library migration failed. See ${env.BUILD_URL} for details.",
                to: 'team@example.com'
            )
        }
    }
}
```

### Azure DevOps Pipeline

Integrate the migration tool into your Azure DevOps pipeline:

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
    - main
  paths:
    include:
    - altium_libraries/**

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.9'
    addToPath: true

- script: pip install altium2kicad
  displayName: 'Install dependencies'

- script: |
    altium2kicad --input altium_libraries/main_library.DbLib \
                 --output kicad_libraries \
                 --library-name MainLibrary \
                 --parallel-processing \
                 --max-workers 4 \
                 --generate-report
  displayName: 'Run migration'

- task: PublishBuildArtifacts@1
  inputs:
    pathtoPublish: 'kicad_libraries'
    artifactName: 'kicad-libraries'
  displayName: 'Publish KiCAD libraries'

- task: PublishBuildArtifacts@1
  inputs:
    pathtoPublish: 'migration_report.html'
    artifactName: 'migration-report'
  displayName: 'Publish migration report'
```

## Webhook Integration

The migration tool can trigger webhooks on various events:

```yaml
# config.yaml
webhooks:
  enabled: true
  endpoints:
    - url: https://example.com/webhook/migration-started
      events: [migration_started]
      headers:
        Authorization: "Bearer your_token"
    - url: https://example.com/webhook/migration-completed
      events: [migration_completed, migration_failed]
      headers:
        Authorization: "Bearer your_token"
  retry:
    max_attempts: 3
    backoff_factor: 2
```

### Webhook Payload Example

```json
{
  "event": "migration_completed",
  "timestamp": "2023-05-15T14:30:45Z",
  "job_id": "job_12345",
  "input": "path/to/library.DbLib",
  "output": "output_directory",
  "library_name": "MyLibrary",
  "stats": {
    "component_count": 1250,
    "success_count": 1245,
    "warning_count": 5,
    "error_count": 0,
    "duration_seconds": 45
  },
  "result_url": "https://example.com/results/job_12345"
}
```

## Version Control Best Practices

### Database Migration Files

When working with database migrations, follow these best practices:

#### Directory Structure

```
project/
├── altium_libraries/
│   ├── main_library.DbLib
│   ├── connector_library.DbLib
│   └── ic_library.DbLib
├── kicad_libraries/
│   ├── main_library.kicad_sym
│   ├── connector_library.kicad_sym
│   └── ic_library.kicad_sym
├── migration_configs/
│   ├── production.yaml
│   ├── development.yaml
│   └── ci.yaml
└── scripts/
    ├── migrate_all.sh
    └── validate_libraries.py
```

#### Git Configuration

Create a `.gitattributes` file to properly handle binary database files:

```
# .gitattributes
*.DbLib binary
*.mdb binary
*.accdb binary
*.sqlite binary
*.kicad_sym text
*.kicad_mod text
```

#### .gitignore Configuration

```
# .gitignore
# Ignore temporary migration files
.altium2kicad_cache/
migration_temp/

# Ignore log files
*.log
logs/

# Ignore generated reports (store these elsewhere)
*_report.html
*_report.json

# Don't ignore KiCAD library files
!*.kicad_sym
!*.kicad_mod
```

### Branching Strategy

For component library migrations, consider this branching strategy:

1. **main**: Contains the latest stable KiCAD libraries
2. **development**: For testing new migrations
3. **feature/component-type**: For adding new component types
4. **hotfix/component-name**: For fixing specific component issues

### Commit Message Conventions

Use structured commit messages for library changes:

```
component(type): add/update/fix component name

- Added new parameters
- Updated footprint reference
- Fixed symbol pin mapping

Refs: ISSUE-123
```

### Pull Request Template

Create a pull request template for library changes:

```markdown
## Component Library Changes

### Type of change
- [ ] New component addition
- [ ] Component update
- [ ] Component fix
- [ ] Library structure change

### Description
Describe the changes made to the component libraries.

### Migration details
- Source Altium library: [library name]
- Target KiCAD library: [library name]
- Number of components affected: [count]

### Validation
- [ ] All components have been validated in KiCAD
- [ ] Footprints match the original designs
- [ ] Symbols follow KiCAD conventions
- [ ] Documentation has been updated

### Screenshots
[If applicable, add screenshots of the components]
```

## Automated Testing

### Component Library Testing

Create automated tests for your component libraries:

```python
# test_libraries.py
import unittest
from altium2kicad.validation import LibraryValidator

class TestComponentLibraries(unittest.TestCase):
    def setUp(self):
        self.validator = LibraryValidator()
    
    def test_resistor_library(self):
        result = self.validator.validate_library("kicad_libraries/resistors.kicad_sym")
        self.assertTrue(result.success)
        self.assertEqual(result.error_count, 0)
    
    def test_capacitor_library(self):
        result = self.validator.validate_library("kicad_libraries/capacitors.kicad_sym")
        self.assertTrue(result.success)
        self.assertEqual(result.error_count, 0)
    
    def test_ic_library(self):
        result = self.validator.validate_library("kicad_libraries/ics.kicad_sym")
        self.assertTrue(result.success)
        self.assertEqual(result.error_count, 0)

if __name__ == "__main__":
    unittest.main()
```

### CI/CD Integration for Testing

Add testing to your CI/CD pipeline:

```yaml
# GitHub Actions example
test_libraries:
  runs-on: ubuntu-latest
  needs: migrate
  steps:
    - uses: actions/checkout@v2
    
    - name: Download KiCAD libraries
      uses: actions/download-artifact@v2
      with:
        name: kicad-libraries
        path: kicad_libraries/
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install altium2kicad pytest
    
    - name: Run tests
      run: pytest test_libraries.py -v
```

## Continuous Deployment

### Automatic Library Publishing

Set up automatic publishing of KiCAD libraries:

```yaml
# GitHub Actions example
publish_libraries:
  runs-on: ubuntu-latest
  needs: test_libraries
  if: github.ref == 'refs/heads/main'
  steps:
    - uses: actions/checkout@v2
    
    - name: Download KiCAD libraries
      uses: actions/download-artifact@v2
      with:
        name: kicad-libraries
        path: kicad_libraries/
    
    - name: Set up Git
      run: |
        git config --global user.name "Library Bot"
        git config --global user.email "bot@example.com"
    
    - name: Commit and push libraries
      run: |
        git add kicad_libraries/
        git commit -m "Update KiCAD libraries [skip ci]"
        git push
    
    - name: Create release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: v${{ github.run_number }}
        release_name: Library Update v${{ github.run_number }}
        body: |
          Automated library update from Altium sources.
          
          See migration report for details.
        draft: false
        prerelease: false
```

## Next Steps

- Review the [Security Best Practices](../user_guide/security.md) for secure integration
- Consult the [Performance Tuning Guide](../user_guide/performance.md) for optimizing automated migrations
- See the [Enterprise Deployment Guide](../user_guide/enterprise.md) for multi-user environments