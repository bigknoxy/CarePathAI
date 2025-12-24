# ADR-0004: FastAPI ML Service Architecture

## Context
Need to design FastAPI endpoints for ML services leveraging existing embedding and vector store components to provide semantic search and orchestration capabilities for healthcare data retrieval.

## Decision
Implement three core endpoints (/embed, /retrieve, /orchestrate) with singleton model loading, in-memory FAISS index, and thread-safe operations.

## Consequences
- **Performance**: Model loaded once at startup, index kept in memory for fast retrieval
- **Scalability**: FAISS IndexFlatL2 is thread-safe for concurrent searches
- **Maintainability**: Clear separation between embedding generation, retrieval, and orchestration logic
- **Reliability**: Graceful degradation when index/model unavailable

## Architecture Decisions

### Model Loading Pattern
- **Singleton**: Load SentenceTransformer once at application startup
- **Lazy Loading**: Initialize on first request if startup loading fails
- **Fallback**: Return 503 when model unavailable

### Index Lifecycle
- **Startup Load**: Load FAISS index and metadata during application startup
- **In-Memory**: Keep index in memory for fast access
- **Reload Capability**: Support on-demand index reloading for updates
- **Thread Safety**: FAISS IndexFlatL2 is thread-safe for read operations

### API Design
- **RESTful**: Clean HTTP verb and path conventions
- **JSON Schema**: Strict request/response validation with Pydantic
- **Error Handling**: Consistent error response format
- **Status Codes**: Appropriate HTTP status codes for all scenarios

### Performance Considerations
- **Batch Processing**: Support embedding multiple texts in single request
- **Configurable Limits**: Default top_k=5, max top_k=100
- **Async Support**: FastAPI async endpoint pattern for concurrency
- **Memory Management**: Monitor embedding size and index memory usage