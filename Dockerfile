FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (asyncmy & pymysql are pure Python, no extra libs needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# WeChat Cloud Hosting injects PORT env var (default 80)
ENV PORT=8000

# Expose port
EXPOSE ${PORT}

# Run the application — use PORT from environment
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
