#!/usr/bin/env python3
"""Health endpoint for CarePathAI ML service."""

import logging
import os
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Response models
class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether embedding model is loaded")
    index_loaded: bool = Field(..., description="Whether FAISS index is loaded")
    data_dir: str = Field(..., description="Data directory path")


class DetailedHealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether embedding model is loaded")
    index_loaded: bool = Field(..., description="Whether FAISS index is loaded")
    data_dir: str = Field(..., description="Data directory path")
    components: Dict[str, Any] = Field(..., description="Detailed component status")


router = APIRouter(prefix="/health", tags=["health"])


def create_health_endpoint(app):
    """Factory function to create endpoint with app context."""

    @router.get("", response_model=HealthResponse)
    async def health_check():
        """
        Basic health check.

        Returns service status and component availability.
        """
        try:
            # Get data directory
            data_dir = os.environ.get("CAREPATH_DATA_DIR", "/app/data")

            # Check component status
            model_loaded = hasattr(app.state, "model") and app.state.model is not None
            index_loaded = hasattr(app.state, "index") and app.state.index is not None

            # Determine overall status
            if model_loaded:
                status_text = "healthy"
            else:
                status_text = "degraded"

            logger.info(
                f"Health check: status={status_text}, model={model_loaded}, index={index_loaded}"
            )

            return HealthResponse(
                status=status_text,
                model_loaded=model_loaded,
                index_loaded=index_loaded,
                data_dir=data_dir,
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthResponse(
                status="unhealthy",
                model_loaded=False,
                index_loaded=False,
                data_dir=os.environ.get("CAREPATH_DATA_DIR", "/app/data"),
            )

    @router.get("/detailed", response_model=DetailedHealthResponse)
    async def detailed_health_check():
        """
        Detailed health check with component information.

        Returns comprehensive status including model details,
        index information, and data directory status.
        """
        try:
            # Get data directory
            data_dir = os.environ.get("CAREPATH_DATA_DIR", "/app/data")
            data_path = Path(data_dir)

            # Check component status
            model_loaded = hasattr(app.state, "model") and app.state.model is not None
            index_loaded = hasattr(app.state, "index") and app.state.index is not None

            # Component details
            components = {
                "model": {
                    "loaded": model_loaded,
                    "type": type(app.state.model).__name__ if model_loaded else None,
                    "status": "ready" if model_loaded else "not_loaded",
                },
                "index": {
                    "loaded": index_loaded,
                    "type": "FAISS IndexFlatL2" if index_loaded else None,
                    "vectors": app.state.index.ntotal if index_loaded else 0,
                    "metadata_count": len(app.state.metadata)
                    if (hasattr(app.state, "metadata") and app.state.metadata)
                    else 0,
                    "status": "ready" if index_loaded else "not_loaded",
                },
                "data_directory": {
                    "path": data_dir,
                    "exists": data_path.exists(),
                    "writable": os.access(data_path, os.W_OK)
                    if data_path.exists()
                    else False,
                    "synthetic_exists": (data_path / "synthetic").exists(),
                    "faiss_exists": (data_path / "faiss").exists(),
                },
            }

            # Determine overall status
            if model_loaded and index_loaded:
                status_text = "healthy"
            elif model_loaded:
                status_text = "degraded"
            else:
                status_text = "unhealthy"

            logger.info(f"Detailed health check: status={status_text}")

            return DetailedHealthResponse(
                status=status_text,
                model_loaded=model_loaded,
                index_loaded=index_loaded,
                data_dir=data_dir,
                components=components,
            )

        except Exception as e:
            logger.error(f"Detailed health check failed: {e}")
            return DetailedHealthResponse(
                status="unhealthy",
                model_loaded=False,
                index_loaded=False,
                data_dir=os.environ.get("CAREPATH_DATA_DIR", "/app/data"),
                components={
                    "error": str(e),
                    "model": {"loaded": False, "status": "error"},
                    "index": {"loaded": False, "status": "error"},
                    "data_directory": {
                        "path": os.environ.get("CAREPATH_DATA_DIR", "/app/data")
                    },
                },
            )

    return router
