FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    apt-get purge -y --auto-remove curl && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.cargo/bin:${PATH}"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy source code
COPY . .

# Ensure static directories exist
RUN mkdir -p static/cards

EXPOSE 8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
