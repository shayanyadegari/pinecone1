# ───────── base image ─────────
FROM python:3.11-slim

# ───────── env & workdir ──────
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# ───────── deps ───────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ───────── source code ────────
COPY . .

# ───────── expose & run ───────
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
