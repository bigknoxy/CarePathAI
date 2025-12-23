#!/usr/bin/env python3
"""Vector store utilities for CarePathAI ML package."""

import logging
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


def build_index(embeddings: np.ndarray):
    """Build FAISS index from embeddings."""
    try:
        import faiss

        if embeddings.ndim != 2:
            raise ValueError(
                f"Expected 2D embeddings array, got shape {embeddings.shape}"
            )

        dim = embeddings.shape[1]
        logger.info(f"Building FAISS IndexFlatL2 with dimension {dim}")

        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)
        logger.info(f"Index built with {index.ntotal} vectors")
        return index
    except ImportError as e:
        logger.error(f"Failed to import faiss: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to build index: {e}")
        raise


def add_to_index(index, embeddings):
    """Add embeddings to existing FAISS index."""
    try:
        if embeddings.ndim != 2:
            raise ValueError(
                f"Expected 2D embeddings array, got shape {embeddings.shape}"
            )

        index.add(embeddings)
        logger.info(
            f"Added {embeddings.shape[0]} vectors to index, total: {index.ntotal}"
        )
    except Exception as e:
        logger.error(f"Failed to add embeddings to index: {e}")
        raise


def save_index(index, path: Path):
    """Save FAISS index to file."""
    try:
        import faiss

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        faiss.write_index(index, str(path))
        logger.info(f"Saved FAISS index to {path}")
    except ImportError as e:
        logger.error(f"Failed to import faiss: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to save index to {path}: {e}")
        raise


def load_index(path: Path):
    """Load FAISS index from file."""
    try:
        import faiss

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Index file not found: {path}")

        index = faiss.read_index(str(path))
        logger.info(f"Loaded FAISS index from {path} with {index.ntotal} vectors")
        return index
    except ImportError as e:
        logger.error(f"Failed to import faiss: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load index from {path}: {e}")
        raise


def load_index_if_exists(path: Path):
    """Load FAISS index from file if it exists, otherwise return None."""
    try:
        path = Path(path)
        if not path.exists():
            logger.warning(f"Index file not found: {path}")
            return None
        return load_index(path)
    except Exception as e:
        logger.error(f"Failed to load index from {path}: {e}")
        return None


def search_index(index, query_embeddings, top_k: int = 10):
    """Search FAISS index for similar embeddings."""
    try:
        if query_embeddings.ndim == 1:
            query_embeddings = query_embeddings.reshape(1, -1)

        if query_embeddings.ndim != 2:
            raise ValueError(
                f"Expected 2D query embeddings, got shape {query_embeddings.shape}"
            )

        distances, indices = index.search(query_embeddings, top_k)
        logger.info(
            f"Search completed: found {len(indices[0])} results for {len(query_embeddings)} queries"
        )
        return distances, indices
    except Exception as e:
        logger.error(f"Failed to search index: {e}")
        raise
