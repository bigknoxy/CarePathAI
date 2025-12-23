#!/usr/bin/env python3
from pathlib import Path
import json
import pickle
import numpy as np
import importlib.util
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Import data_paths module directly
data_paths_path = Path(__file__).parent / "utils" / "data_paths.py"
spec = importlib.util.spec_from_file_location("data_paths", data_paths_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load data_paths from {data_paths_path}")
data_paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data_paths)
get_data_paths = data_paths.get_data_paths

# Mock ingestion using scikit-learn as fallback when sentence-transformers fails
DATA_DIR, INDEX_DIR = get_data_paths()


def load_texts(data_dir):
    """Load text data from patient JSON files"""
    texts = []
    meta = []
    for f in sorted(data_dir.glob("patient_*.json")):
        with open(f) as fh:
            obj = json.load(fh)
            texts.append(obj.get("notes", ""))
            meta.append({"id": obj.get("id"), "mrn": obj.get("medicalRecordNumber")})
    return texts, meta


def create_mock_index(texts, meta):
    """Create a mock index using TF-IDF vectors"""
    print("Creating mock index with TF-IDF...")

    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(max_features=384, stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(texts)

    # Create mock index structure
    mock_index = {
        "vectors": tfidf_matrix.toarray(),
        "vectorizer": vectorizer,
        "metadata": meta,
        "dim": tfidf_matrix.shape[1],
    }

    # Save mock index
    mock_index_path = INDEX_DIR / "patient_index.mock"
    with open(mock_index_path, "wb") as f:
        pickle.dump(mock_index, f)

    # Save metadata
    with open(INDEX_DIR / "metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2)

    return mock_index_path


def main():
    """Main ingestion function"""
    print("Starting mock ingestion (TF-IDF fallback)...")

    try:
        # Try real FAISS ingestion first
        from sentence_transformers import SentenceTransformer
        import faiss

        print("Using sentence-transformers for real FAISS index...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        texts, meta = load_texts(DATA_DIR)
        print(f"Loaded {len(texts)} documents")

        embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)

        faiss.write_index(index, str(INDEX_DIR / "patient_index.faiss"))
        with open(INDEX_DIR / "metadata.json", "w") as fh:
            json.dump(meta, fh, indent=2)

        print("✅ Real FAISS index created successfully!")
        return "real"

    except Exception as e:
        print(f"❌ FAISS ingestion failed: {e}")
        print("🔄 Falling back to mock index...")

        # Fallback to mock index
        texts, meta = load_texts(DATA_DIR)
        print(f"Loaded {len(texts)} documents")

        mock_path = create_mock_index(texts, meta)
        print(f"✅ Mock index created: {mock_path}")
        return "mock"


if __name__ == "__main__":
    result = main()
    print(f"\nIngestion complete. Result: {result} index created.")
