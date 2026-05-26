FROM python:3.11-slim

WORKDIR /app
# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv venv && uv pip install -e .

# Copy source code
COPY src ./src

CMD ["uv", "run", "python", "src/worker.py"]
