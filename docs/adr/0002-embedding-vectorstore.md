# ADR 0002 - Embeddings & Vector Store: FAISS with sentence-transformers

## Context

CarePath AI needs a reproducible, local-first retrieval system to support RAG. Cloud vector DBs are production-ready but introduce cost and complexity for a portfolio demo.

## Decision

Use `sentence-transformers` (all-MiniLM-L6-v2) for embeddings and FAISS (faiss-cpu) for local vector storage. Persist FAISS index files to disk so they can be included in Docker volumes and reused across runs.

## Consequences

- Pros:
  - Fully reproducible locally without external services
  - Low-cost for demo use
  - Fast enough for prototype retrieval tasks

- Cons:
  - Not a managed solution; ops responsibilities (backup, scaling) fall on the owner.
  - For larger datasets or production load, a managed vector DB (Pinecone, Milvus, Weaviate) would be preferable.

## Status

Accepted

## Date

2025-12-22
