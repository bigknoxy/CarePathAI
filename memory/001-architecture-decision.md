Context:

Need to balance enterprise engineering with ML ecosystem for an applied prototype.

Decision:

Use C# for orchestration and Python for ML, communicate via REST for demo simplicity, propagate OpenTelemetry traces.

Outcome:

Pros:
- Leverages best-of-breed tooling: C# for typed orchestration and middleware, Python for ML libraries and experimentation.
- Demonstrates cross-stack integration valuable for hiring/portfolio reviews.
- Keeps local demo reproducible (local embeddings + FAISS) without cloud dependencies.

Cons:
- Adds cross-service integration complexity and more surface area for testing and observability.
- Slightly higher local setup complexity (Docker Compose) compared to a single-process demo.

Acceptance: Accepted
