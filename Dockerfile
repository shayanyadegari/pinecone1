# ───────── base image ─────────
FROM python:3.11-slim

# ───────── env & workdir ──────
ENV PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:${PATH}"
WORKDIR /app

# ───────── install pipx & uv ───
RUN pip install --no-cache-dir pipx \
 && pipx install uv

# ───────── install deps via uv ──
# use --system because there's no venv here
RUN uv pip install --system --no-cache-dir \
      fastapi \
      uvicorn \
      fastapi-mcp \
      python-dotenv \
      openai \
      pydantic \
      pinecone

# ───────── install mcp-proxy tool ─
RUN uv tool install mcp-proxy

# ───────── copy source ─────────
COPY . .

# ───────── set app dir ─────────

# ───────── expose & run ───────
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
