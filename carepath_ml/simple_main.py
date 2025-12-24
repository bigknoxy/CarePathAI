#!/usr/bin/env python3
"""Main FastAPI application for CarePathAI ML service."""

import logging
import json
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from carepath_ml.embeddings import load_model
from carepath_ml.vector_store import load_index_if_exists
from carepath_ml.endpoints.embed import create_embed_endpoint
from carepath_ml.endpoints.retrieve import create_retrieve_endpoint
from carepath_ml.endpoints.orchestrate import create_orchestrate_endpoint
from carepath_ml.health import create_health_endpoint

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown."""
    # Startup logic
    logger.info("Starting CarePath ML Service...")

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Get data directory
    data_dir = Path(os.environ.get("CAREPATH_DATA_DIR", "/app/data"))
    index_dir = data_dir / "faiss"

    logger.info(f"Using data directory: {data_dir}")

    try:
        # Load embedding model (singleton pattern)
        logger.info("Loading embedding model...")
        model = load_model()
        app.state.model = model
        logger.info(f"Model loaded successfully: {type(model).__name__}")

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        app.state.model = None

    try:
        # Load FAISS index if exists
        logger.info("Loading FAISS index...")
        index = load_index_if_exists(index_dir / "patient_index.faiss")
        if index is not None:
            app.state.index = index
            logger.info(f"FAISS index loaded with {index.ntotal} vectors")
        else:
            app.state.index = None
            logger.warning("FAISS index not found, retrieval will be limited")

    except Exception as e:
        logger.error(f"Failed to load index: {e}")
        app.state.index = None

    try:
        # Load metadata
        metadata_path = index_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            app.state.metadata = metadata
            logger.info(f"Metadata loaded: {len(metadata)} entries")
        else:
            app.state.metadata = []
            logger.warning(f"Metadata file not found: {metadata_path}")

    except Exception as e:
        logger.error(f"Failed to load metadata: {e}")
        app.state.metadata = []

    logger.info("Startup complete")

    yield

    # Shutdown logic
    logger.info("Shutting down CarePath ML Service...")


# Create FastAPI app
app = FastAPI(
    title="CarePath AI ML Service",
    description="Healthcare AI service for embeddings, retrieval, and care orchestration",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(create_health_endpoint(app), prefix="/api/v1")
app.include_router(create_embed_endpoint(app), prefix="/api/v1")
app.include_router(create_retrieve_endpoint(app), prefix="/api/v1")
app.include_router(create_orchestrate_endpoint(app), prefix="/api/v1")


# Legacy compatibility routes (non-prefixed)
@app.get("/health")
async def health_legacy():
    """Legacy health endpoint for backward compatibility."""
    return {"status": "ok", "service": "CarePath ML Service"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
