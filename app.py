import os
from typing import List
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from openai import OpenAI
from fastapi_mcp import FastApiMCP

# Import your Pinecone wrapper
from pinecone_doc_store import PineconeDocStore
from fastapi.security.api_key import APIKeyHeader
from fastapi import Depends, Security
from fastapi import Request

# load environment variables from .env
load_dotenv()

# ────────────────── FastAPI app ──────────────────
app = FastAPI()

# ────────────────── OpenAI client ─────────────────
oai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ────────────────── Pinecone doc store settings ───
INDEX_NAME = os.getenv("PINECONE_INDEX", "receptional")
NAMESPACE  = os.getenv("PINECONE_NAMESPACE", "ns1")
AUTH_API   = os.getenv("AUTH_API","")


async def verify_api_key(request: Request):

    auth = request.headers.get("Authorization")

    if auth != f"Bearer {AUTH_API}":
        raise HTTPException(status_code=401, detail="invalid or missing API key")



# ─────────────── API models ─────────────
class QueryParams(BaseModel):
    query: str
    top_k: int = 3


class Answer(BaseModel):
    context: List[str]


# ──────────────── routes ───────────────
@app.get("/vector_client", response_model=Answer,
         dependencies=[Depends(verify_api_key)])
def ask(
    query: str = Query(..., min_length=1, description="Text to search"),
    top_k: int = Query(3, ge=1, le=20, description="Number of results to return")
):

    # initialise your Pinecone store
    store = PineconeDocStore(
        index_name=INDEX_NAME,
        namespace=NAMESPACE,
    )

    # guard against empty query (though Query(..., min_length=1) already enforces)
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty")

    # fetch matches
    matches = store.query(query, top_k=top_k)
    context = [m.metadata.get("text", "") for m in matches]

    return Answer(context=context)


# ─── expose endpoints as MCP tools ───
mcp = FastApiMCP(
    app,
    name="query about clients",
    description="if user ask any name and you didnt know check this tools that has vector db about clients"
)
mcp.mount()


# ────────────────── local run ────────────────────
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host=host, port=port)
