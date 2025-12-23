from fastapi import FastAPI

app = FastAPI(title="CarePath ML Service", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/detailed")
async def health_detailed():
    return {
        "status": "ok",
        "service": "CarePath ML Service",
        "version": "1.0.0",
        "indices": {
            "faiss_available": False,
            "faiss_loaded": False,
            "faiss_exists": True,
            "metadata_count": 100,
            "mock_index_available": True,
            "mock_index_count": 100,
        },
        "model": {"name": "basic", "loaded": True},
        "paths": {
            "data_dir": "/data/synthetic",
            "index_dir": "/data/faiss",
            "metadata_file": "/data/faiss/metadata.json",
            "mock_index_file": "/data/faiss/patient_index.mock",
            "faiss_index_file": "/data/faiss/patient_index.faiss",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
