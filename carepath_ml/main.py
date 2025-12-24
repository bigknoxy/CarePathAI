import logging
import json
import pickle
from typing import Optional
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel

# Import data_paths module directly
data_paths_path = Path(__file__).parent / "utils" / "data_paths.py"
import importlib.util

spec = importlib.util.spec_from_file_location("data_paths", data_paths_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load data_paths from {data_paths_path}")
data_paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data_paths)
get_data_paths = data_paths.get_data_paths

app = FastAPI(title="CarePath ML Service", version="1.0.0")
logger = logging.getLogger(__name__)

# Import the new endpoints dynamically
import importlib.util
from pathlib import Path

# Load embed endpoint
embed_path = Path(__file__).parent / "endpoints" / "embed.py"
embed_spec = importlib.util.spec_from_file_location("embed_endpoint", embed_path)
if embed_spec is None or embed_spec.loader is None:
    raise ImportError("Could not load embed endpoint")
embed_module = importlib.util.module_from_spec(embed_spec)
embed_spec.loader.exec_module(embed_module)
embed_router = embed_module.router

# Load orchestrate endpoint
orchestrate_path = Path(__file__).parent / "endpoints" / "orchestrate.py"
orchestrate_spec = importlib.util.spec_from_file_location(
    "orchestrate_endpoint", orchestrate_path
)
if orchestrate_spec is None or orchestrate_spec.loader is None:
    raise ImportError("Could not load orchestrate endpoint")
orchestrate_module = importlib.util.module_from_spec(orchestrate_spec)
orchestrate_spec.loader.exec_module(orchestrate_module)
orchestrate_router = orchestrate_module.router

# Global state for index usage
USE_FAISS = False
FAISS_INDEX = None
METADATA_LIST = None
MODEL = None
MOCK_INDEX = None
MODEL_NAME = "all-MiniLM-L6-v2"


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
    global USE_FAISS, FAISS_INDEX, METADATA_LIST, MOCK_INDEX, MODEL

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
        "model": {"name": MODEL_NAME, "loaded": MODEL is not None},
        "paths": {
            "data_dir": str(get_data_paths()[0]),
            "index_dir": str(get_data_paths()[1]),
        },
    }

    return health_info


@app.post("/admin/refresh-index")
async def admin_refresh_index():
    """Refresh/rebuild the FAISS index and metadata."""
    global USE_FAISS, FAISS_INDEX, METADATA_LIST

    try:
        import subprocess
        import sys

        # Run the ingest script to rebuild the index
        ingest_script = Path(__file__).parent / "ingest.py"

        logger.info("Starting index refresh via ingest.py")
        result = subprocess.run(
            [sys.executable, str(ingest_script)],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            logger.error(f"Index refresh failed: {result.stderr}")
            return {
                "success": False,
                "message": "Index refresh failed",
                "error": result.stderr,
                "stdout": result.stdout,
            }

        # Reload the index in memory
        logger.info("Reloading index after refresh")
        USE_FAISS, FAISS_INDEX = load_index()
        load_metadata()

        return {
            "success": True,
            "message": "Index refreshed successfully",
            "faiss_loaded": FAISS_INDEX is not None,
            "metadata_count": len(METADATA_LIST) if METADATA_LIST else 0,
            "stdout": result.stdout,
        }

    except subprocess.TimeoutExpired:
        logger.error("Index refresh timed out")
        return {"success": False, "message": "Index refresh timed out after 5 minutes"}
    except Exception as e:
        logger.error(f"Index refresh error: {e}")
        return {"success": False, "message": f"Index refresh error: {str(e)}"}


def load_index():
    """
    Load FAISS index from disk if available.

    Returns:
        Tuple of (use_faiss_bool, index_obj_or_none)
    """
    try:
        data_dir, index_dir = get_data_paths(force_package_local=False)
        faiss_path = index_dir / "patient_index.faiss"

        if faiss_path.exists():
            import faiss

            index = faiss.read_index(str(faiss_path))
            logger.info(f"USING_FAISS: loaded patient_index.faiss from {faiss_path}")
            return True, index
        else:
            logger.info(
                f"FAISS index not found at {faiss_path}. Falling back to TF-IDF mock index."
            )
            return False, None

    except Exception as e:
        logger.error(
            f"Failed to load FAISS index: {e}. Falling back to TF-IDF mock index."
        )
        return False, None


def load_metadata():
    """Load metadata from JSON file."""
    global METADATA_LIST
    try:
        data_dir, index_dir = get_data_paths(force_package_local=False)
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
        data_dir, index_dir = get_data_paths(force_package_local=False)
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


def get_model():
    """Lazy load sentence-transformers model."""
    global MODEL
    if MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer

            MODEL = SentenceTransformer(MODEL_NAME)
            logger.info(f"Loaded sentence-transformers model: {MODEL_NAME}")
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers model: {e}")
            MODEL = None
    return MODEL


def search_faiss(query: str, top_k: int = 5) -> list[dict]:
    """Search using FAISS index."""
    global FAISS_INDEX, METADATA_LIST

    if FAISS_INDEX is None or METADATA_LIST is None:
        logger.error("FAISS index or metadata not available")
        return []

    try:
        model = get_model()
        if model is None:
            logger.error("Sentence-transformers model not available")
            return []

        # Encode query
        query_embedding = model.encode([query], convert_to_numpy=True)

        # Search FAISS index
        distances, indices = FAISS_INDEX.search(
            query_embedding, min(top_k, len(METADATA_LIST))
        )

        # Build results
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx >= 0 and idx < len(METADATA_LIST):  # Valid index
                metadata = METADATA_LIST[idx]
                results.append(
                    {
                        "id": metadata.get("id"),
                        "mrn": metadata.get("mrn"),
                        "score": float(dist),  # L2 distance (lower is better)
                        "snippet": f"Document {metadata.get('id')}",  # Could be enhanced with actual text
                    }
                )

        logger.info(f"FAISS search returned {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"FAISS search failed: {e}")
        return []


def search_tfidf(query: str, top_k: int = 5) -> list[dict]:
    """Search using TF-IDF fallback."""
    global MOCK_INDEX

    if MOCK_INDEX is None:
        logger.warning("Mock index not available, returning empty results")
        return []

    try:
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = MOCK_INDEX["vectorizer"]
        tfidf_matrix = MOCK_INDEX["vectors"]
        metadata = MOCK_INDEX["metadata"]

        # Transform query
        query_vector = vectorizer.transform([query])

        # Compute similarities
        similarities = cosine_similarity(query_vector, tfidf_matrix)[0]

        # Get top-k indices
        top_indices = similarities.argsort()[-top_k:][::-1]

        # Build results
        results = []
        for idx in top_indices:
            if idx < len(metadata):
                meta = metadata[idx]
                results.append(
                    {
                        "id": meta.get("id"),
                        "mrn": meta.get("mrn"),
                        "score": float(
                            similarities[idx]
                        ),  # Cosine similarity (higher is better)
                        "snippet": f"Document {meta.get('id')}",  # Could be enhanced with actual text
                    }
                )

        logger.info(f"TF-IDF search returned {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"TF-IDF search failed: {e}")
        return []


@app.on_event("startup")
async def startup_event():
    """Initialize global state on application startup."""
    global USE_FAISS, FAISS_INDEX, METADATA_LIST

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Load FAISS index
    USE_FAISS, FAISS_INDEX = load_index()

    # Load metadata and mock index
    load_metadata()
    load_mock_index()

    # Store model and index in app.state for new endpoints
    app.state.model = get_model()
    app.state.index = FAISS_INDEX
    app.state.metadata = METADATA_LIST

    # Include new API endpoints
    app.include_router(embed_router)
    app.include_router(orchestrate_router)

    logger.info(
        f"Startup complete - USE_FAISS={USE_FAISS}, FAISS_INDEX loaded={FAISS_INDEX is not None}"
    )


@app.post("/retrieve")
async def retrieve(request: QueryRequest):
    """Retrieve documents based on query."""
    top_k = request.top_k or 5

    if USE_FAISS and FAISS_INDEX is not None:
        logger.info(f"Retrieving using FAISS (top_k={top_k})")
        results = search_faiss(request.query, top_k)
    else:
        logger.info(f"Retrieving using TF-IDF fallback (top_k={top_k})")
        results = search_tfidf(request.query, top_k)

    return QueryResponse(results=results)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
