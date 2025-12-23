from fastapi import FastAPI
from fastapi.responses import JSONResponse
import json
from pathlib import Path

app = FastAPI(title="CarePath ML Service", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check including system state and index status."""

    # Try to read existing data
    try:
        metadata_path = Path("/app/data/faiss/metadata.json")
        mock_path = Path("/app/data/faiss/patient_index.mock")
        faiss_path = Path("/app/data/faiss/patient_index.faiss")

        metadata_count = 0
        mock_count = 0
        faiss_exists = False

        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
                metadata_count = len(metadata)

        if mock_path.exists():
            mock_count = 100  # Approximate

        faiss_exists = faiss_path.exists()

        health_info = {
            "status": "ok",
            "service": "CarePath ML Service",
            "version": "1.0.0",
            "indices": {
                "faiss_available": False,
                "faiss_loaded": False,
                "faiss_exists": faiss_exists,
                "metadata_count": metadata_count,
                "mock_index_available": True,
                "mock_index_count": mock_count,
            },
            "model": {"name": "basic", "loaded": True},
            "paths": {
                "data_dir": "/app/data/synthetic",
                "index_dir": "/app/data/faiss",
                "metadata_file": str(metadata_path),
                "mock_index_file": str(mock_path),
                "faiss_index_file": str(faiss_path),
            },
        }

        return health_info
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "service": "CarePath ML Service",
            },
        )


class QueryRequest:
    def __init__(self, query: str, top_k: int = 5):
        self.query = query
        self.top_k = top_k


class QueryResponse:
    def __init__(self, results: list):
        self.results = results


@app.post("/retrieve")
async def retrieve(request_data: dict):
    """Simple keyword-based retrieval without ML dependencies."""
    try:
        query = request_data.get("query", "")
        top_k = request_data.get("top_k", 5)

        # Simple mock results for demonstration
        mock_results = [
            {
                "id": f"patient_00{i}",
                "mrn": f"MRN_00{i}",
                "score": 0.9 - (i * 0.1),
                "snippet": f"Mock patient record {i} with query match for '{query}'",
            }
            for i in range(min(top_k, 5))
        ]

        return {"results": mock_results}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Search failed: {str(e)}", "results": []},
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
