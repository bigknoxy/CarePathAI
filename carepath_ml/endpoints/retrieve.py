#!/usr/bin/env python3
"""Retrieve endpoint for CarePathAI ML service."""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Request/Response models
class RetrieveRequest(BaseModel):
    query: str = Field(..., description="Query text for retrieval")
    top_k: Optional[int] = Field(
        5, description="Number of results to return", ge=1, le=100
    )


class RetrieveResult(BaseModel):
    id: int = Field(..., description="Document ID")
    score: float = Field(..., description="Similarity score (L2 distance)")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    text: str = Field(..., description="Document text")


class RetrieveResponse(BaseModel):
    query: str = Field(..., description="Original query")
    results: List[RetrieveResult] = Field(..., description="Retrieved documents")
    distance_metric: str = Field(..., description="Distance metric used")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")


router = APIRouter(prefix="/retrieve", tags=["retrieval"])


def create_retrieve_endpoint(app):
    """Factory function to create endpoint with app context."""

    @router.post("", response_model=RetrieveResponse)
    async def retrieve_documents(request: RetrieveRequest):
        """
        Retrieve documents based on query similarity.

        Uses FAISS index with L2 distance for similarity search.
        Returns documents with metadata and similarity scores.
        """
        try:
            # Validate index is loaded
            if not hasattr(app.state, "index") or app.state.index is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={"error": "Search index not available"},
                )

            # Validate model is loaded
            if not hasattr(app.state, "model") or app.state.model is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={"error": "Embedding model not loaded"},
                )

            index = app.state.index
            model = app.state.model
            metadata = app.state.metadata

            # Generate query embedding
            logger.info(f"Generating embedding for query: {request.query[:100]}...")
            query_embedding = model.encode([request.query], convert_to_numpy=True)

            # Search index (Thread-safe: FAISS search is read-only and thread-safe)
            logger.info(f"Searching index for top_k={request.top_k}")
            # Use FAISS search directly to avoid import issues
            distances, indices = index.search(query_embedding, request.top_k)

            # Process results
            results = []
            query_results = indices[0]  # First (and only) query
            query_distances = distances[0]

            for i, (idx, dist) in enumerate(zip(query_results, query_distances)):
                if idx >= 0 and idx < len(metadata):  # Valid index
                    meta_entry = metadata[idx].copy()
                    result = RetrieveResult(
                        id=int(idx),
                        score=float(dist),
                        metadata=meta_entry,
                        text=meta_entry.get("text", f"Document {idx}"),
                    )
                    results.append(result)
                else:
                    logger.warning(f"Invalid index {idx} in search results")

            logger.info(f"Returning {len(results)} results for query")

            return RetrieveResponse(
                query=request.query, results=results, distance_metric="L2"
            )

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": f"Retrieval failed: {str(e)}"},
            )

    return router
