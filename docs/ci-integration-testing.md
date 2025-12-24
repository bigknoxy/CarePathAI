# GitHub Actions Integration Testing

## Overview

The CarePathAI integration testing pipeline builds and runs all services in Docker containers, executes the full pytest integration suite, and provides comprehensive artifacts for debugging.

## Workflow Location

`.github/workflows/integration-tests.yml`

## How It Works

### 1. Environment Setup
- **Runner**: Ubuntu latest with Docker support
- **Cache Handling**: Creates `ml_cache` and `.workspace/data` directories with proper permissions
- **Image Building**: Builds `carepath_ml` service with `UID:1001:GID:1001` for non-root execution

### 2. Service Orchestration
- **Build**: `docker compose build --no-cache` ensures fresh builds
- **Startup**: `docker compose up -d` starts all services (db, ml, api, ui, prometheus)
- **Health Checks**: Sequential waiting with timeouts:
  - PostgreSQL: 90s timeout
  - ML Service: 120s timeout (longer due to model loading)
  - API Service: 90s timeout
  - UI Service: 90s timeout (optional verification)

### 3. Test Execution
```bash
pytest tests/integration/ \
  -m integration \
  --json-report \
  --json-report-file=.integration-logs/pytest_integration_report.json \
  --verbose \
  --tb=short
```

### 4. Environment Variables
- `CAREPATH_DATA_DIR`: `/home/runner/work/CarePathAI/CarePathAI/.workspace/data`
- `API_BASE_URL`: `http://localhost:5000`
- `ML_BASE_URL`: `http://localhost:8000`

## Viewing Artifacts

### In GitHub Actions UI
1. Navigate to the Actions tab in your repository
2. Select the workflow run
3. Click "Artifacts" section
4. Download `integration-test-results`

### Artifacts Contents
```
.integration-logs/
├── pytest_integration_report.json  # Structured test results
├── pytest_output.txt              # Full console output
├── docker_compose_logs.txt        # Complete service logs
└── SUMMARY.md                      # This explanation file
```

### Using Test Results
- **Pass/Fail Status**: Workflow status shows overall test result
- **Detailed Logs**: `pytest_output.txt` contains full test execution details
- **JSON Analysis**: `pytest_integration_report.json` for programmatic parsing
- **Service Debugging**: `docker_compose_logs.txt` for container-level issues

## Known Limitations & Solutions

### 1. Runner Docker Support
- **Issue**: GitHub-hosted runners don't provide privileged Docker by default
- **Solution**: Uses `services: docker` with privileged mode
- **Alternative**: Self-hosted runners with Docker-in-Docker if issues persist

### 2. Cache Permissions
- **Issue**: ML service requires proper permissions for `/cache` volume
- **Solution**: Creates directories with `777` permissions and runs as `UID:1001:GID:1001`

### 3. Timeout Management
- **Issue**: ML service loading can take time
- **Solution**: 120s timeout for ML service, 90s for others
- **Adjustment**: Modify timeout values if services take longer

### 4. Large Docker Pulls
- **Issue**: Base images can be large (PyTorch, PostgreSQL)
- **Solution**: Build with `--no-cache` ensures consistency
- **Optimization**: Consider using smaller base images or layer caching in future

## Running Locally

To replicate CI behavior locally:

```bash
# Set up directories
mkdir -p ml_cache .workspace/data
chmod 777 ml_cache .workspace/data

# Build and start services
docker compose build --no-cache
docker compose up -d

# Set environment variables
export CAREPATH_DATA_DIR=$(pwd)/.workspace/data
export API_BASE_URL=http://localhost:5000
export ML_BASE_URL=http://localhost:8000

# Run tests
pytest tests/integration/ -m integration --json-report --json-report-file=test-results.json

# Cleanup
docker compose down -v
```

## Troubleshooting

### Common Issues

1. **Permission Denied**:
   ```bash
   # Fix cache permissions
   sudo chown -R 1001:1001 ml_cache
   chmod -R 755 ml_cache
   ```

2. **Service Not Ready**:
   - Check `docker compose logs <service>`
   - Increase timeout values in workflow

3. **Test Environment Issues**:
   - Verify environment variables in workflow run
   - Check `.integration-logs/pytest_output.txt` for detailed errors

4. **Build Failures**:
   - Review Docker build logs in workflow output
   - Check for base image updates or dependency changes

### Getting Help

1. **Workflow Logs**: Check the "Actions" tab for detailed step-by-step execution
2. **Artifacts**: Download logs for offline analysis
3. **Local Reproduction**: Use the local reproduction commands above

## Performance Notes

- **Build Time**: ~5-8 minutes (Docker image building)
- **Test Time**: ~2-5 minutes (integration test execution)
- **Total Runtime**: ~15-20 minutes (including cleanup)
- **Timeout**: 30 minutes overall workflow timeout

For optimization requests or issues, update the workflow file and document changes in this README.