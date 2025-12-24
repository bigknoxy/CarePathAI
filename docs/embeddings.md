Embeddings — CarePath AI ML Service

Overview

- Model: sentence-transformers "all-MiniLM-L6-v2" (default used by the service)
- Embedding dimension: 384
- Vector store: FAISS (L2 distance)
- Default FAISS index location: <CAREPATH_DATA_DIR>/faiss/patient_index.faiss (when running in-container: /app/data/faiss/patient_index.faiss)

Environment variables

- CAREPATH_DATA_DIR — base path for data and indices. Default: /app/data inside container. When set, index files are written to $CAREPATH_DATA_DIR/faiss
- API_BASE_URL — base URL for the C# API used by the orchestrate endpoint. Default: http://localhost:5000
- TRANSFORMERS_CACHE / HF_HOME — optional caches for Hugging Face / sentence-transformers. Set these to control disk cache locations if you are pulling models at runtime.

Endpoints

1) POST /api/v1/embed

- Purpose: generate a single embedding for an input text
- Request (JSON):
  {
    "text": "<your text to embed>"
  }
- Example curl (ML service running on localhost:8000):
  curl -s -X POST "http://localhost:8000/api/v1/embed" \
    -H "Content-Type: application/json" \
    -d '{"text":"History of present illness: patient with chest pain"}'

- Expected response (200):
  {
    "embedding": [0.00012, -0.1234, ...],
    "dim": 384
  }

- Common error codes:
  - 400 Bad Request: invalid/missing text
  - 503 Service Unavailable: model not loaded
  - 500 Internal Server Error: unexpected failure while generating embedding

Notes:
- The embed endpoint lazily loads the sentence-transformers model if it is not already available in app state. This reduces startup time but requires the container has network access to download the model or that a cached copy exists in TRANSFORMERS_CACHE / HF_HOME.


2) POST /api/v1/retrieve

- Purpose: retrieve documents similar to a query using the FAISS index
- Request (JSON):
  {
    "query": "patient with high blood pressure",
    "top_k": 5
  }
- Example curl:
  curl -s -X POST "http://localhost:8000/api/v1/retrieve" \
    -H "Content-Type: application/json" \
    -d '{"query":"hypertension", "top_k":3}'

- Expected response (200):
  {
    "query": "hypertension",
    "results": [
      {"id": 12, "score": 0.4321, "metadata": {...}, "text": "..."},
      {"id": 5, "score": 0.5432, "metadata": {...}, "text": "..."}
    ],
    "distance_metric": "L2"
  }

- Notes:
  - If the FAISS index is not loaded, retrieval will be limited or fallback logic may be used (see troubleshooting).


3) POST /api/v1/orchestrate

- Purpose: orchestrate a patient-level retrieval flow by fetching patient data from the main API and running retrieval to return relevant documents
- Request (JSON):
  {
    "patient_id": 123,
    "top_k": 5
  }
- Example curl:
  curl -s -X POST "http://localhost:8000/api/v1/orchestrate" \
    -H "Content-Type: application/json" \
    -d '{"patient_id":123, "top_k":5}'

- Expected response (200):
  {
    "patient": {"id":123, "firstName":"John", "lastName":"Doe", ...},
    "retrieved": [{"id": 1, "score": 0.34, "text": "...", "metadata": {...}}, ...]
  }

- Error handling:
  - 404 Not Found: patient not found in the C# API
  - 502 Bad Gateway: downstream C# API error
  - 500 Internal Server Error: unexpected internal failure


How ingestion works (building the FAISS index)

- Script: carepath_ml/scripts/ingest_embeddings.py
- Default behavior (inside container): reads JSON patient files from /app/data/synthetic and writes FAISS index + metadata to /app/data/faiss
- Default output files:
  - patient_index.faiss
  - metadata.json

- Example (from integration run):
  export CAREPATH_DATA_DIR="/home/josh/projects/CarePathAI/carepath_ml/data"
  docker compose run --rm ml bash -lc "python /app/scripts/ingest_embeddings.py --input_dir /app/data/synthetic --output_dir /app/data/faiss"

- Local (no container) example:
  python carepath_ml/scripts/ingest_embeddings.py --input_dir carepath_ml/data/synthetic --output_dir /tmp/faiss

- The ingestion script:
  - loads the sentence-transformers model (all-MiniLM-L6-v2)
  - encodes texts in batches (default batch_size=32)
  - builds a FAISS index (L2)
  - atomically writes the index and metadata using temporary files (writes .faiss.tmp / .json.tmp then renames)

Where logs and test artifacts are stored

- Integration and CI logs generated during local runs are written to the repository-level directory: .integration-logs/
- Notable files produced during the last integration run:
  - .integration-logs/pytest_integration_report.json (integration test results summary)
  - .integration-logs/commands_run.sh (commands used to set up and run)
  - .integration-logs/ingestion_ls.txt (index dir listing)
  - .integration-logs/health_ml.txt, health_api.txt
  - .integration-logs/README and SUMMARY files

Troubleshooting — common errors and fixes

1) Missing sentence-transformers or other Python deps
- Symptoms: ImportError mentioning sentence_transformers or faiss
- Fix: pip install -r carepath_ml/requirements.txt (or install sentence-transformers and faiss-cpu). For development use the project's pyproject.toml or test_and_build.sh in carepath_ml.

2) CAREPATH_DATA_DIR permission or path errors
- Symptoms: RuntimeError: No writable data directory found OR index/metadata not created
- Fixes:
  - Ensure CAREPATH_DATA_DIR points to a writable absolute path, or leave unset to use package-local carepath_ml/data
  - For container runs, set CAREPATH_DATA_DIR in your environment or docker-compose.yml to a host path mounted into the container and writable by the container user

3) FAISS index not found or retrieval returns empty
- Symptoms: /retrieve returns 503 or empty results
- Fix:
  - Run ingestion script to create patient_index.faiss and metadata.json in the configured faiss dir
  - Verify file presence: ls $CAREPATH_DATA_DIR/faiss
  - Check permissions — ingestion uses atomic write: it writes a .faiss.tmp and renames; failures can leave temp files which should be removed before retry

4) Orchestrate upstream errors (C# API)
- Symptoms: /api/v1/orchestrate returns 502 or 404
- Fix:
  - Ensure API_BASE_URL points to the running C# API (default http://localhost:5000)
  - Check the API health endpoint and /api/patients/{id}

5) Model lazy-load delays or download timeouts
- Symptoms: First call to /api/v1/embed is slow or times out while downloading the model
- Fixes:
  - Pre-warm model at startup by setting up the ML service to load the model (simple_main.py already attempts to load model during startup)
  - Provision TRANSFORMERS_CACHE / HF_HOME with the model present to avoid downloads at runtime

6) Tests report endpoints missing (historical)
- The integration test report may show skip reasons such as: "Embed endpoint not available in basic ML service". If you see this, ensure you're running the full ML service (not a minimal/basic image) and that the ML container is built from carepath_ml/Dockerfile with basic_main.py or simple_main.py which include the embed and orchestrate endpoints.

Integration test runbook (reproduce locally)

1) Prepare environment
- From repo root:
  export UID=$(id -u)
  export GID=$(id -g)
  mkdir -p ./ml_cache; chmod 0755 ./ml_cache
  export CAREPATH_DATA_DIR="/absolute/path/to/writable/data"  # e.g. /home/josh/projects/CarePathAI/carepath_ml/data

2) Build and run containers
- docker compose build --no-cache
- MY_UID=$(id -u) MY_GID=$(id -g) docker compose up -d

3) (If needed) Rebuild ML service and run only ML container for debugging
- MY_UID=$(id -u) MY_GID=$(id -g) docker compose build --no-cache ml
- MY_UID=$(id -u) MY_GID=$(id -g) docker compose up -d --force-recreate ml

4) Ensure ingestion has run (creates FAISS index)
- docker compose run --rm ml bash -lc "python /app/scripts/ingest_embeddings.py --input_dir /app/data/synthetic --output_dir /app/data/faiss"

5) Run integration tests (from repo root)
- pytest -q tests/integration/test_carepath_services.py

6) Inspect integration results and logs
- .integration-logs/pytest_integration_report.json
- .integration-logs/commands_run.sh
- ML logs: .integration-logs/ml.log (if present)

Files of interest in the codebase

- carepath_ml/endpoints/embed.py — embed endpoint implementation
- carepath_ml/endpoints/retrieve.py — retrieval implementation
- carepath_ml/endpoints/orchestrate.py — orchestrate endpoint implementation
- carepath_ml/scripts/ingest_embeddings.py — ingestion script that builds the FAISS index
- carepath_ml/utils/data_paths.py — logic for resolving CAREPATH_DATA_DIR and faiss index location
- .integration-logs/ — integration artifacts and test reports

If anything here is out of date or you want CLI examples for different host/port combinations, tell me what URL/ports you are using and I will add adjusted curl examples.
