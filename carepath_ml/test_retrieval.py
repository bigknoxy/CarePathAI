#!/usr/bin/env python3
"""
Test script for ML service retrieval functionality.
Tests both FAISS and TF-IDF search methods.
"""

import json
import asyncio
import logging
from typing import Dict, List, Any

# Test queries
TEST_QUERIES = [
    {"query": "diabetes medication", "top_k": 3},
    {"query": "heart disease", "top_k": 2},
    {"query": "patient with hypertension", "top_k": 5},
    {"query": "chest pain", "top_k": 1},
]


async def test_retrieval(base_url: str = "http://localhost:8000"):
    """Test the /retrieve endpoint with various queries."""
    import httpx

    print(f"🧪 Testing ML Service at {base_url}")
    print("=" * 50)

    async with httpx.AsyncClient() as client:
        # Test health endpoint first
        try:
            response = await client.get(f"{base_url}/health")
            print(f"✅ Health check: {response.json()}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return

        # Test retrieval endpoints
        for i, test_case in enumerate(TEST_QUERIES, 1):
            print(f"\n🔍 Test {i}: {test_case}")

            try:
                response = await client.post(
                    f"{base_url}/retrieve", json=test_case, timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    results = result.get("results", [])

                    print(f"✅ Status: {response.status_code}")
                    print(f"📊 Results count: {len(results)}")

                    for j, item in enumerate(results, 1):
                        print(
                            f"  {j}. ID: {item.get('id')}, MRN: {item.get('mrn')}, Score: {item.get('score'):.4f}"
                        )
                        print(f"     Snippet: {item.get('snippet')}")

                else:
                    print(f"❌ Status: {response.status_code}")
                    print(f"Response: {response.text}")

            except Exception as e:
                print(f"❌ Request failed: {e}")


def test_functions_locally():
    """Test the search functions directly without HTTP."""
    print("🧪 Testing search functions locally")
    print("=" * 50)

    # Import the main module
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))

    try:
        from main import (
            search_faiss,
            search_tfidf,
            load_metadata,
            load_mock_index,
        )

        # Initialize global state
        load_metadata()
        load_mock_index()

        for test_case in TEST_QUERIES:
            query = test_case["query"]
            top_k = test_case["top_k"]

            print(f"\n🔍 Query: '{query}' (top_k={top_k})")

            # Test TF-IDF search
            tfidf_results = search_tfidf(query, top_k)
            print(f"📊 TF-IDF results: {len(tfidf_results)}")
            for result in tfidf_results:
                print(f"  - ID: {result.get('id')}, Score: {result.get('score'):.4f}")

            # Note: FAISS testing would require the actual FAISS index
            # This would work if the index exists

    except Exception as e:
        print(f"❌ Local function testing failed: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test ML Service retrieval")
    parser.add_argument(
        "--mode",
        choices=["http", "local", "both"],
        default="both",
        help="Test mode: http endpoint, local functions, or both",
    )
    parser.add_argument(
        "--url", default="http://localhost:8000", help="Base URL for HTTP testing"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    if args.mode in ["local", "both"]:
        test_functions_locally()

    if args.mode in ["http", "both"]:
        asyncio.run(test_retrieval(args.url))
