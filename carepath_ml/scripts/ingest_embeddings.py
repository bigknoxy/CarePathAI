#!/usr/bin/env python3
"""CLI script for ingesting embeddings and building FAISS index."""

import argparse
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_texts(data_dir):
    """Load patient texts and metadata from JSON files."""
    import json

    texts = []
    meta = []
    patient_files = list(data_dir.glob("patient_*.json"))

    if not patient_files:
        logger.warning(f"No patient JSON files found in {data_dir}")
        return texts, meta

    logger.info(f"Loading {len(patient_files)} patient files from {data_dir}")

    for f in sorted(patient_files):
        try:
            with open(f) as fh:
                obj = json.load(fh)
                texts.append(obj.get("notes", ""))
                meta.append(
                    {"id": obj.get("id"), "mrn": obj.get("medicalRecordNumber")}
                )
        except Exception as e:
            logger.error(f"Failed to load patient file {f}: {e}")
            continue

    logger.info(f"Successfully loaded {len(texts)} documents")
    return texts, meta


def atomic_write_index(index, index_path):
    """Atomically write FAISS index using temporary file + rename."""
    import faiss

    temp_path = index_path.with_suffix(".faiss.tmp")
    try:
        faiss.write_index(index, str(temp_path))
        temp_path.rename(index_path)
        logger.info(f"Atomically wrote FAISS index to {index_path}")
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        logger.error(f"Failed to atomically write FAISS index: {e}")
        raise


def atomic_write_metadata(metadata, metadata_path):
    """Atomically write metadata JSON using temporary file + rename."""
    import json

    temp_path = metadata_path.with_suffix(".json.tmp")
    try:
        with open(temp_path, "w") as fh:
            json.dump(metadata, fh, indent=2)
        temp_path.rename(metadata_path)
        logger.info(f"Atomically wrote metadata to {metadata_path}")
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        logger.error(f"Failed to atomically write metadata: {e}")
        raise


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest embeddings and build FAISS index"
    )
    parser.add_argument(
        "--input_dir",
        type=Path,
        default=Path("/app/data/synthetic"),
        help="Input directory containing patient JSON files",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=Path("/app/data/faiss"),
        help="Output directory for FAISS index and metadata",
    )

    args = parser.parse_args()

    try:
        # Import required dependencies
        from carepath_ml.embeddings import load_model, embed_texts
        from carepath_ml.vector_store import build_index

        # Ensure directories exist
        args.input_dir.mkdir(parents=True, exist_ok=True)
        args.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Loading sentence transformer model...")
        model = load_model()

        logger.info(f"Loading texts from {args.input_dir}...")
        texts, meta = load_texts(args.input_dir)

        if not texts:
            logger.error("No texts loaded - cannot create index")
            return 1

        logger.info(f"Generating embeddings for {len(texts)} documents...")
        embeddings = embed_texts(model, texts, batch_size=32)

        if embeddings.size == 0:
            logger.error("Failed to generate embeddings")
            return 1

        logger.info("Building FAISS index...")
        index = build_index(embeddings)

        logger.info("Writing index files...")
        index_path = args.output_dir / "patient_index.faiss"
        metadata_path = args.output_dir / "metadata.json"

        # Atomic writes
        atomic_write_index(index, index_path)
        atomic_write_metadata(meta, metadata_path)

        logger.info(f"Successfully created index at {args.output_dir}")
        logger.info(f"Index contains {len(meta)} patient records")
        logger.info(f"Embedding dimension: {embeddings.shape[1]}")

        return 0

    except ImportError as e:
        logger.error(f"Missing dependencies: {e}")
        logger.error("Please run: pip install -r requirements.txt")
        return 1
    except Exception as e:
        logger.error(f"Failed to create index: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
