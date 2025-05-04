from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec, Index

load_dotenv()  # load variables from .env if present


@dataclass
class Document:
    """Container for one document to be indexed."""

    text: str
    metadata: Dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Pinecone + OpenAI document store
# ---------------------------------------------------------------------------


class PineconeDocStore:
    """Simple wrapper for embedding, upserting and querying text docs."""

    def __init__(
        self,
        index_name: str = "doc-index",
        namespace: str = "default",
        dimension: int = 1536,
        metric: str = "cosine",
        cloud: str = "aws",
        region: str = "us-east-1",
    ) -> None:
       
        # Keys from env vars as fallback
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if not self.openai_api_key or not self.pinecone_api_key:
            raise RuntimeError("OPENAI_API_KEY and PINECONE_API_KEY must be set")

        # Clients
        self._oai = OpenAI(api_key=self.openai_api_key)
        self._pc = Pinecone(api_key=self.pinecone_api_key)

        self.index_name = index_name
        self.namespace = namespace
        self.dimension = dimension
        self.metric = metric

        # Ensure index exists (serverless)
  

        self._index = self._pc.Index(index_name)

    # ---------------------------------------------------------------------
    # Embeddings
    # ---------------------------------------------------------------------

    def _embed(self, text: str) -> List[float]:
        """Get OpenAI embedding for a piece of text."""
        res = self._oai.embeddings.create(
            model="text-embedding-3-small",
            input=[text],
        )
        return res.data[0].embedding


    # ---------------------------------------------------------------------
    # Querying
    # ---------------------------------------------------------------------

    def query(self, text: str, top_k: int = 5, filter: Optional[dict] = None) -> List[dict]:
        """Return Pinecone matches for a text query."""
        emb = self._embed(text)
        res = self._index.query(
            vector=emb,
            top_k=top_k,
            include_metadata=True,
            namespace=self.namespace,
            #filter=filter or {},
        )
        return res.matches
