# ADR 0001 - Separation of Concerns: C# Orchestration + Python ML Service

## Context

CarePath AI needs to demonstrate both enterprise-grade engineering practices and modern ML/AI capabilities. A single-language monolith would simplify deployment but would hide the ML tooling ecosystem and reduce authenticity as an applied ML project.

## Decision

Use a hybrid architecture:

- CarePath.Api (.NET): handles API surface, orchestration, authentication/authorization, background jobs, audit logging, observability, and integration patterns.
- CarePath.ML (Python FastAPI): handles embeddings, vector store, retrieval, prompt orchestration, and safety guardrails.

The two services communicate over HTTP (REST) for ease-of-demo and simplicity, with OpenTelemetry traces propagated across calls.

## Consequences

- Pros:
  - Leverages best tooling for each responsibility (C# for typed orchestration and middleware, Python for ML libs).
  - Demonstrates cross-stack integration—the kind of system design hiring managers want to see.
  - Keeps local demo reproducible (Python local embeddings + FAISS).

- Cons:
  - Introduces cross-service integration complexity and requires careful observability and testing across the boundary.
  - Slightly more setup for local development (Docker Compose), but acceptable for a portfolio project.

## Status

Accepted

## Date

2025-12-22
