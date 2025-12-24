# FastAPI ML Service API Contract

## Endpoints

### POST /embed
Generate embeddings for text input(s).

**Request Schema:**
```json
{
  "text": "string"  // Single text input
}
```
OR
```json
{
  "texts": ["string", "..."]  // Multiple text inputs
}
```

**Response Schema:**
```json
{
  "embeddings": [[0.1, 0.2, ...], ...],  // Array of embedding vectors
  "model_name": "all-MiniLM-L6-v2",      // Model used
  "dimensions": 384,                      // Embedding dimensions
  "count": 1                              // Number of embeddings generated
}
```

**Status Codes:**
- 200: Success
- 400: Bad request (missing text/texts, invalid input)
- 500: Internal server error (model loading failure)
- 503: Service unavailable (model not loaded)

### POST /retrieve
Search for similar documents using FAISS index.

**Request Schema:**
```json
{
  "query": "string",    // Search query text
  "top_k": 5           // Number of results (default: 5, max: 100)
}
```

**Response Schema:**
```json
{
  "query": "string",                    // Original query
  "top_k": 5,                          // Number requested
  "distance_metric": "L2",             // Distance metric used
  "results": [
    {
      "id": 1,                         // Document ID from metadata
      "score": 0.123,                  // L2 distance (lower = more similar)
      "metadata": {                    // Document metadata from metadata.json
        "mrn": "MRN001"
      },
      "text": "document text content"   // Full document text
    }
  ],
  "total_available": 100,              // Total documents in index
  "search_time_ms": 15                 // Search latency
}
```

**Status Codes:**
- 200: Success
- 400: Bad request (missing query, invalid top_k)
- 404: Index not loaded
- 500: Internal server error (search failure)

### POST /orchestrate
Retrieve and summarize context for patient queries.

**Request Schema:**
```json
{
  "patient_id": 123,      // Patient identifier
  "query": "string",      // Clinical query
  "top_k": 5             // Number of results (default: 5)
}
```

**Response Schema:**
```json
{
  "patient": {
    "patient_id": 123,
    "status": "found"     // "found" | "not_found" | "error"
  },
  "retrieval": {
    "query": "string",
    "top_k": 5,
    "results_count": 5,
    "search_time_ms": 12
  },
  "retrieved": [          // Raw retrieval results
    {
      "id": 1,
      "score": 0.123,
      "metadata": {"mrn": "MRN001"},
      "text": "document text"
    }
  ],
  "summary": {
    "model_name": "mock-summary-v1",
    "evidence_count": 5,
    "summary_text": "Based on the retrieved documents, key findings include...",
    "confidence": 0.85
  },
  "processing_time_ms": 45
}
```

**Status Codes:**
- 200: Success
- 400: Bad request (missing patient_id or query)
- 404: Patient not found or index not loaded
- 500: Internal server error

## Error Response Schema

All endpoints return consistent error format:

```json
{
  "error": "Human readable error message",
  "error_code": "MISSING_FIELD",
  "timestamp": "2025-12-24T10:30:00Z",
  "request_id": "uuid-for-tracking"
}
```

## Health and Metrics Endpoints

### GET /health
Overall service health check.

**Response:**
```json
{
  "status": "healthy",           // "healthy" | "degraded" | "unhealthy"
  "timestamp": "2025-12-24T10:30:00Z",
  "version": "0.0.1",
  "components": {
    "model": "loaded",           // "loaded" | "loading" | "error"
    "index": "loaded",           // "loaded" | "loading" | "error"
    "metadata": "loaded"         // "loaded" | "loading" | "error"
  }
}
```

### GET /metrics
Service metrics for monitoring.

**Response:**
```json
{
  "timestamp": "2025-12-24T10:30:00Z",
  "model": {
    "name": "all-MiniLM-L6-v2",
    "dimensions": 384,
    "loaded_at": "2025-12-24T09:00:00Z"
  },
  "index": {
    "total_vectors": 100,
    "dimension": 384,
    "index_type": "IndexFlatL2",
    "loaded_at": "2025-12-24T09:00:00Z",
    "cache_path": "/app/data/faiss/patient_index.faiss"
  },
  "requests": {
    "total_embeddings": 1500,
    "total_retrievals": 800,
    "total_orchestrations": 300,
    "avg_embedding_time_ms": 25,
    "avg_search_time_ms": 8
  }
}
```

## Implementation Details

### Model Configuration
- **Default Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Loading**: Singleton instance at startup
- **Thread Safety**: Model is thread-safe for inference

### Index Configuration
- **FAISS Index**: IndexFlatL2 for exact L2 distance search
- **Metadata**: JSON file with ID-to-metadata mapping
- **Distance Metric**: L2 distance (lower scores = more similar)
- **Thread Safety**: IndexFlatL2 is thread-safe for concurrent searches

### Performance Specifications
- **Concurrent Requests**: Support up to 50 concurrent embeddings
- **Batch Size**: Maximum 32 texts per request for embeddings
- **Top K Limits**: 1-100 results per retrieval request
- **Timeout**: 30 seconds for embedding generation, 5 seconds for search

### Cache Strategy
- **Model**: In-memory singleton (no cache invalidation needed)
- **Index**: In-memory with optional reload endpoint
- **Metadata**: In-memory JSON array
- **Metrics**: In-memory counters with periodic persistence