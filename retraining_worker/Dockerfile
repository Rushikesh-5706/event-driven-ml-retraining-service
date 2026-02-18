FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker/ ./worker

# Expected to be mounted via docker-compose, but we copy for standalone build safety
# In production, data might come from S3 or valid mount
COPY data/ ./data 

# Unbuffered output for seeing logs in real-time
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "worker.consumer"]
