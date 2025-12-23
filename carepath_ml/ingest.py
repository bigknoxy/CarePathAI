#!/usr/bin/env python3
import logging
import json
import sys
from pathlib import Path
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import data_paths module directly
data_paths_path = Path(__file__).parent / "utils" / "data_paths.py"
spec = importlib.util.spec_from_file_location("data_paths", data_paths_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load data_paths from {data_paths_path}")
data_paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data_paths)
get_data_paths = data_paths.get_data_paths

MODEL_NAME = "all-MiniLM-L6-v2"
# Get data paths from helper module
DATA_DIR, INDEX_DIR = get_data_paths()


def load_texts(data_dir):
    """Load patient texts and metadata from JSON files."""
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
    """Main ingest function that creates FAISS index with atomic writes."""
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        import faiss
    except ImportError as e:
        logger.error(f"Missing dependencies: {e}")
        logger.error("Please run: pip install -r requirements.txt")
        return False

    try:
        # Ensure directories exist
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        INDEX_DIR.mkdir(parents=True, exist_ok=True)

        logger.info(f"Loading sentence-transformers model: {MODEL_NAME}")
        model = SentenceTransformer(MODEL_NAME)

        logger.info("Loading texts and metadata...")
        texts, meta = load_texts(DATA_DIR)

        if not texts:
            logger.error("No texts loaded - cannot create index")
            return False

        logger.info(f"Generating embeddings for {len(texts)} documents...")
        embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        dim = embeddings.shape[1]

        logger.info(f"Creating FAISS index with dimension {dim}")
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)

        logger.info("Writing index files...")
        index_path = INDEX_DIR / "patient_index.faiss"
        metadata_path = INDEX_DIR / "metadata.json"

        # Atomic writes
        atomic_write_index(index, index_path)
        atomic_write_metadata(meta, metadata_path)

        logger.info(f"Successfully created index at {INDEX_DIR}")
        logger.info(f"Index contains {len(meta)} patient records")

        return True

    except Exception as e:
        logger.error(f"Failed to create index: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
