#!/usr/bin/env python3
"""Embeddings utilities for CarePathAI ML package."""

import logging
from typing import List
import numpy as np

logger = logging.getLogger(__name__)


def load_model(model_name: str = "all-MiniLM-L6-v2"):
    """Load sentence transformer model."""
    try:
        from sentence_transformers import SentenceTransformer

        logger.info(f"Loading model: {model_name}")
        model = SentenceTransformer(model_name)
        logger.info("Model loaded successfully")
        return model
    except ImportError as e:
        logger.error(f"Failed to import sentence_transformers: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise


def embed_texts(model, texts: List[str], batch_size: int = 32) -> np.ndarray:
    """Generate embeddings for a list of texts using the provided model."""
    if not texts:
        logger.warning("No texts provided for embedding")
        return np.array([])

    try:
        logger.info(
            f"Generating embeddings for {len(texts)} texts with batch_size={batch_size}"
        )
        embeddings = model.encode(
            texts, batch_size=batch_size, show_progress_bar=True, convert_to_numpy=True
        )
        logger.info(f"Generated embeddings with shape: {embeddings.shape}")
        return embeddings
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise


def save_embeddings(path, embeddings):
    """Save embeddings to numpy file."""
    try:
        import numpy as np

        np.save(path, embeddings)
        logger.info(f"Saved embeddings to {path}")
    except Exception as e:
        logger.error(f"Failed to save embeddings to {path}: {e}")
        raise
