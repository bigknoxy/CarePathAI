#!/usr/bin/env python3
"""Embeddings endpoint for CarePathAI ML service."""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Request model
class EmbedRequest(BaseModel):
    text: str = Field(..., description="Text to embed", min_length=1, max_length=10000)


# Response model
class EmbedResponse(BaseModel):
    embedding: List[float] = Field(..., description="Generated embedding vector")
    dim: int = Field(..., description="Dimension of the embedding")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")


router = APIRouter(prefix="/api/v1", tags=["embeddings"])


def validate_embed_text(text: str) -> None:
    """
    Validate input text for embedding.

    Args:
        text: Input text to validate

    Raises:
        ValueError: If text is invalid
    """
    if not isinstance(text, str):
        raise ValueError("Text must be a string")
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    if len(text) > 10000:
        raise ValueError("Text too long (max 10000 characters)")


def generate_embedding(text: str, model) -> List[float]:
    """
    Generate embedding for given text using the provided model.

    Args:
        text: Text to embed
        model: Sentence transformer model

    Returns:
        List of embedding values

    Raises:
        RuntimeError: If embedding generation fails
    """
    try:
        embedding = model.encode([text], convert_to_numpy=True)
        return embedding[0].tolist()
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise RuntimeError(f"Embedding generation failed: {str(e)}")


@router.post("/embed", response_model=EmbedResponse)
async def embed_text(request: Request, embed_request: EmbedRequest):
    """
    Generate embedding for input text.

    Accepts JSON body: {"text": "..."}
    Returns embedding with dimension: {"embedding": [float,...], "dim": 384}
    """
    try:
        # Validate input
        validate_embed_text(embed_request.text)

        # Get model from app state or load lazily
        if not hasattr(request.app.state, "model") or request.app.state.model is None:
            # Lazy load model using relative import
            import sys
            from pathlib import Path

            embeddings_path = Path(__file__).parent.parent / "embeddings.py"
            import importlib.util

            spec = importlib.util.spec_from_file_location("embeddings", embeddings_path)
            if spec is None or spec.loader is None:
                raise RuntimeError("Could not load embeddings module")

            embeddings_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(embeddings_module)
            request.app.state.model = embeddings_module.load_model()

        model = request.app.state.model
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "Embedding model not available"},
            )

        # Generate embedding
        embedding = generate_embedding(embed_request.text, model)

        # Get dimension - safe approach
        dim = len(embedding)  # default
        if hasattr(model, "get_sentence_embedding_dimension"):
            try:
                dim_result = model.get_sentence_embedding_dimension()
                if isinstance(dim_result, (int, float)):
                    dim = int(dim_result)
            except Exception:
                pass  # stick with default

        logger.info(
            f"Generated embedding for text (length={len(embed_request.text)}, dim={dim})"
        )

        return EmbedResponse(embedding=embedding, dim=dim)

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in embed_text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
