from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="CarePath ML Service", version="1.0.0")


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    results: list


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/retrieve")
async def retrieve(request: QueryRequest):
    return QueryResponse(results=[])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
