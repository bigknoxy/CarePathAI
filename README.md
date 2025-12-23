# CarePathAI

An AI system that ingests healthcare-style data and generates personalized care guidance, summaries, and routing recommendations using RAG and multi-step orchestration.

## Quick Start

### Docker Compose (Recommended)

Build and run all services:
```bash
docker-compose up --build
```

Run data ingestion:
```bash
docker-compose exec ml python scripts/ingest_embeddings.py
```

Services will be available at:
- API: `http://localhost:5000`
- UI: `http://localhost:5001` 
- ML Service: `http://localhost:8000`
- Prometheus: `http://localhost:9090`

### .NET API

Build the solution:
```bash
dotnet build
```

Run the API:
```bash
dotnet run --project CarePath.Api
```

Run tests:
```bash
dotnet test
```

### Python ML Service

Navigate to the ML service directory and set up the virtual environment:
```bash
cd carepath_ml
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run the ML service:
```bash
python simple_main.py
```

Run tests:
```bash
python -m pytest tests/
```

Run data ingestion:
```bash
python scripts/ingest_embeddings.py
```

## Service Endpoints

### API (`http://localhost:5000`)
- `/health` - Health check
- `/api/patients` - Get patients list

### ML Service (`http://localhost:8000`)
- `/health` - Health check
- `/health/detailed` - Detailed health with index status
- `/retrieve` - Query retrieval endpoint
- `/admin/refresh-index` - Rebuild search index

## Architecture

- **CarePath.Api** - ASP.NET Core Web API for main application logic
- **CarePath.UI** - Blazor Server application for user interface
- **CarePath.Domain** - Domain models and DTOs
- **CarePath.Api.Tests** - Unit tests for the API
- **CarePath.ML** - Python FastAPI service for ML operations

## Docs
- docs/original-project-doc.md
