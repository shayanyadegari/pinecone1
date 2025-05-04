import os
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel

# Import the wrapper built in pinecone_doc_store.py (same folder or installed module)
from pinecone_doc_store import PineconeDocStore

load_dotenv()

# ────────────────── FastAPI app ──────────────────
app = FastAPI(title="Vector QA API (Pinecone)", version="1.0")

# ────────────────── OpenAI client ─────────────────
oai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ────────────────── Pinecone doc store ────────────
DOCS_DIR = os.getenv("DOCS_DIR", "alldocs")
INDEX_NAME = os.getenv("PINECONE_INDEX", "receptional")
NAMESPACE = os.getenv("PINECONE_NAMESPACE", "ns1")




# ─────────────── API models & route ─────────────
class Query(BaseModel):
    query: str
    top_k: int = 3


class Answer(BaseModel):
    context: List[str]
    answer: str


@app.post("/ask", response_model=Answer, summary="Ask a question using vector retrieval")
def ask(query: Query):

    store = PineconeDocStore(
    index_name=INDEX_NAME,
    namespace=NAMESPACE,
    )
    
    if not query.query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty")

    # Retrieve relevant chunks from Pinecone
    matches = store.query(query.query, top_k=query.top_k)
    context = [m.metadata.get("text", "") for m in matches]

    # Compose prompt for GPT
    prompt = (
        "You are a helpful assistant. Use the following context to answer.\n\n"
        "Context:\n" + "\n".join(f"- {c}" for c in context) + "\n\n" +
        f"Question: {query.query}"
    )

    resp = oai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    answer_text = resp.choices[0].message.content.strip()

    return Answer(context=context, answer=answer_text)


# ────────────────── local run ────────────────────
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
