import logging
import json
import pickle
from typing import Optional
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel


# Direct data paths without package dependencies
def get_data_paths():
    data_dir = Path("/data/synthetic")
    index_dir = Path("/data/faiss")
    return data_dir, index_dir


app = FastAPI(title="CarePath ML Service", version="1.0.0")
logger = logging.getLogger(__name__)

# Global state
USE_FAISS = False
FAISS_INDEX = None
METADATA_LIST = None
MOCK_INDEX = None


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class QueryResponse(BaseModel):
    results: list[dict]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check including system state and index status."""
    global USE_FAISS, FAISS_INDEX, METADATA_LIST, MOCK_INDEX

    health_info = {
        "status": "ok",
        "service": "CarePath ML Service",
        "version": "1.0.0",
        "indices": {
            "faiss_available": USE_FAISS,
            "faiss_loaded": FAISS_INDEX is not None,
            "metadata_count": len(METADATA_LIST) if METADATA_LIST else 0,
            "mock_index_loaded": MOCK_INDEX is not None,
            "mock_index_count": len(MOCK_INDEX["metadata"]) if MOCK_INDEX else 0,
        },
        "model": {"name": "basic", "loaded": True},
        "paths": {
            "data_dir": str(get_data_paths()[0]),
            "index_dir": str(get_data_paths()[1]),
        },
    }

    return health_info


def load_metadata():
    """Load metadata from JSON file."""
    global METADATA_LIST
    try:
        data_dir, index_dir = get_data_paths()
        metadata_path = index_dir / "metadata.json"

        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                METADATA_LIST = json.load(f)
            logger.info(f"Loaded {len(METADATA_LIST)} metadata entries")
        else:
            logger.warning(f"Metadata file not found at {metadata_path}")
            METADATA_LIST = []
    except Exception as e:
        logger.error(f"Failed to load metadata: {e}")
        METADATA_LIST = []


def load_mock_index():
    """Load TF-IDF mock index if available."""
    global MOCK_INDEX
    try:
        data_dir, index_dir = get_data_paths()
        mock_path = index_dir / "patient_index.mock"

        if mock_path.exists():
            with open(mock_path, "rb") as f:
                MOCK_INDEX = pickle.load(f)
            logger.info(
                f"Loaded TF-IDF mock index with {len(MOCK_INDEX['metadata'])} documents"
            )
            return True
        else:
            logger.warning(f"Mock index not found at {mock_path}")
            return False
    except Exception as e:
        logger.error(f"Failed to load mock index: {e}")
        return False


def search_tfidf(query: str, top_k: int = 5) -> list[dict]:
    """Search using TF-IDF fallback."""
    global MOCK_INDEX

    if MOCK_INDEX is None:
        logger.warning("Mock index not available, returning empty results")
        return []

    try:
        # Simple keyword search as fallback
        metadata = MOCK_INDEX["metadata"]
        query_lower = query.lower()

        results = []
        for meta in metadata:
            # Simple text matching in patient data
            match_score = 0
            for key, value in meta.items():
                if isinstance(value, str) and query_lower in value.lower():
                    match_score += 1

            if match_score > 0:
                results.append(
                    {
                        "id": meta.get("id"),
                        "mrn": meta.get("mrn"),
                        "score": float(match_score),
                        "snippet": f"Matched {match_score} fields for patient {meta.get('id')}",
                    }
                )

        # Sort by score and take top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:top_k]

        logger.info(f"Keyword search returned {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []


@app.on_event("startup")
async def startup_event():
    """Initialize global state on application startup."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Load metadata and mock index
    load_metadata()
    load_mock_index()

    logger.info(
        f"Startup complete - USE_FAISS={USE_FAISS}, FAISS_INDEX loaded={FAISS_INDEX is not None}"
    )


@app.post("/retrieve")
async def retrieve(request: QueryRequest):
    """Retrieve documents based on query."""
    top_k = request.top_k or 5

    logger.info(f"Retrieving using keyword search (top_k={top_k})")
    results = search_tfidf(request.query, top_k)

    return QueryResponse(results=results)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
