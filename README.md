# CarePathAI

An AI system that ingests healthcare-style data and generates personalized care guidance, summaries, and routing recommendations using RAG and multi-step orchestration.

## Quick Start

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

The API will be available at `http://localhost:5000` with endpoints:
- `/health` - Health check
- `/api/patients` - Get patients list

### Python ML Service

Navigate to the ML service directory and set up the virtual environment:
```bash
cd CarePath.ML
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run the ML service:
```bash
python main.py
```

Run tests:
```bash
python -m pytest
```

The ML service will be available at `http://localhost:8000` with endpoints:
- `/health` - Health check
- `/retrieve` - Query retrieval endpoint

## Architecture

- **CarePath.Api** - ASP.NET Core Web API for main application logic
- **CarePath.UI** - Blazor Server application for user interface
- **CarePath.Domain** - Domain models and DTOs
- **CarePath.Api.Tests** - Unit tests for the API
- **CarePath.ML** - Python FastAPI service for ML operations

## Docs
- docs/original-project-doc.md
