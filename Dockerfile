FROM python:3.11-slim

# Copy uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependencies first
COPY pyproject.toml uv.lock* ./

# Install dependencies (Ensure fastapi, uvicorn, and nicegui are in your pyproject.toml)
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy the entire src directory into the container
COPY src/ ./src/

EXPOSE 80
ENV PYTHONPATH=/app/src

# Run Uvicorn and point it to the app instance in src/insightshub/s.py
# --reload-dir ensures Uvicorn watches the right folder for hot-swapping
CMD ["uvicorn", "insightshub.server:app", "--host", "0.0.0.0", "--port", "80", "--reload", "--reload-dir", "/app/src"]