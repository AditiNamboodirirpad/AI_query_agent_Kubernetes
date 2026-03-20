FROM python:3.11-slim

# Security: run as non-root user
RUN useradd --create-home appuser

WORKDIR /app

# Install dependencies before copying source (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY main.py .

# Create logs directory with correct ownership
RUN mkdir -p logs && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
