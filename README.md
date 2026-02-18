# Event-Driven Asynchronous ML Model Retraining Service

## Overview
This project implements a robust, event-driven backend system for asynchronously triggering machine learning model retraining. It leverages **Flask** for the API gateway, **RabbitMQ** for message queuing, and **Docker** for containerization. The system is designed to handle high-throughput retraining requests without blocking the main application flow, ensuring scalability and resilience.

## Architecture
The system follows a microservices architecture with three main components:

1.  **Training Trigger API (`training_trigger_api`)**:
    -   **Role**: Producer.
    -   **Tech**: Python, Flask, Pika.
    -   **Responsibility**: Accepts RESTful POST requests, validates the payload, and publishes persistent messages to the `retraining_queue`.
    -   **Resilience**: Implements connection retry logic and health checks.

2.  **Message Queue (`rabbitmq`)**:
    -   **Role**: Broker.
    -   **Tech**: RabbitMQ (3-management-alpine).
    -   **Responsibility**: Decouples the API from the Worker, ensuring message durability and reliable delivery.

3.  **Retraining Worker (`retraining_worker`)**:
    -   **Role**: Consumer.
    -   **Tech**: Python, Scikit-Learn, Pandas, Pika.
    -   **Responsibility**: Consumes messages, simulates a resource-intensive ML training process using a dummy dataset, and logs the results.
    -   **Resilience**: Uses manual message acknowledgment (`ack`) to ensure no data loss on failure. Handles failures with dead-lettering logic (simulated via strict NACK).

## Directory Structure
```
.
├── docker-compose.yml          # Orchestration for all services
├── .env                        # Environment variables
├── training_trigger_api/       # API Service Code
│   ├── app/                    # Flask Application
│   ├── tests/                  # API Unit Tests
│   └── Dockerfile
├── retraining_worker/          # Worker Service Code
│   ├── worker/                 # Consumer & ML Logic
│   ├── tests/                  # Worker Unit Tests
│   └── Dockerfile
└── data/                       # Shared Data Directory
    └── dummy_dataset.csv       # Synthetic Dataset
```

## Setup & Installation

### Prerequisites
-   **Docker** and **Docker Compose** installed.
-   **Git** (optional, for cloning).

### running the Application
1.  **Clone the repository** (if applicable):
    ```bash
    git clone <repo_url>
    cd event-driven-ml-retraining
    ```

2.  **Start the services**:
    ```bash
    docker-compose up -d --build
    ```
    This command builds the images and starts the containers in detached mode.

3.  **Verify Status**:
    ```bash
    docker-compose ps
    ```
    Ensure all three services (`rabbitmq`, `training_trigger_api`, `retraining_worker`) are `healthy` or `running`.

## Usage

### Trigger Retraining
To trigger a model retraining job, send a POST request to the API:

```bash
curl -X POST http://localhost:5000/trigger-retraining \
     -H "Content-Type: application/json" \
     -d '{"model_id": "model_v1", "dataset_version": "v1.0"}'
```

**Expected Response (202 Accepted):**
```json
{
  "message": "Retraining triggered successfully",
  "model_id": "model_v1",
  "status": "success"
}
```

### Monitor Progress
Check the worker logs to see the training simulation:
```bash
docker-compose logs -f retraining_worker
```
**Sample Output:**
```
INFO - Received task: Retrain model_v1 (Data: v1.0)
INFO - Starting training for model model_v1...
INFO - Training completed. Model: model_v1, Accuracy: 0.8500
INFO - Task successfully processed. Acknowledging message.
```

## Testing

### Automated E2E Verification
A script `verify_system.py` is included to verify the entire flow automatically:
```bash
# Requires python requests
python verify_system.py
```

### Running Unit Tests
Unit tests are located in the `tests/` directory of each service. You can run them locally:

1.  **Install Dependencies**:
    ```bash
    pip install -r training_trigger_api/requirements.txt
    pip install -r retraining_worker/requirements.txt
    ```

2.  **Run API Tests**:
    ```bash
    export PYTHONPATH=$PYTHONPATH:$(pwd)/training_trigger_api
    python -m unittest discover training_trigger_api/tests
    ```

3.  **Run Worker Tests**:
    ```bash
    export PYTHONPATH=$PYTHONPATH:$(pwd)/retraining_worker
    python -m unittest discover retraining_worker/tests
    ```

## Design Decisions
-   **Event-Driven**: Decoupling the training request from execution allows the API to remain responsive (~ms latency) even if training takes hours.
-   **Durability**: RabbitMQ queues are declared `durable=True` and messages are `persistent`. If the broker restarts, messages are safe.
-   **Reliability**: The worker uses manual acknowledgments. If the worker crashes mid-process, the message remains in the queue and will be redelivered to another worker.
-   **Configuration**: All credentials and hostnames are managed via `.env` file and Docker environment variables, preventing hardcoded secrets.
-   **Structure**: `training_trigger_api` and `retraining_worker` are isolated contexts, promoting separation of concerns.

## Future Improvements
-   **Dead Letter Queue (DLQ)**: Implement a DLQ for messages that fail processing after N retries (currently we Nack without requeue to prevent loops).
-   **Metrics**: robust metrics (Prometheus) to track queue depth and training time.
-   **Shared Storage**: Use S3 or a shared volume for the dataset in a real production environment instead of a local file copy.
