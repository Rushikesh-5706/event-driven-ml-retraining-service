FROM python:3.9-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
