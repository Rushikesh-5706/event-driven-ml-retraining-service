import pika
import os
import json
import logging
import sys
import time
from pika.exceptions import AMQPConnectionError
from .model_trainer import ModelTrainer

# Configure structured logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

logging.basicConfig(level=logging.INFO)
root_logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
root_logger.addHandler(handler)
# Remove default handlers
for h in root_logger.handlers[:-1]:
    root_logger.removeHandler(h)

logger = logging.getLogger(__name__)

# Config
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')
QUEUE_NAME = 'retraining_queue'

def get_connection():
    """Attempts to connect to RabbitMQ with retries."""
    retries = 0
    max_retries = 10
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )

    while retries < max_retries:
        try:
            logger.info(f"Attempting connection to RabbitMQ ({RABBITMQ_HOST}:{RABBITMQ_PORT})...")
            connection = pika.BlockingConnection(parameters)
            return connection
        except AMQPConnectionError as e:
            sleep_time = min(5 * (2 ** retries), 60) # Exponential backoff capped at 60s
            logger.warning(f"Connection failed: {e}. Retrying in {sleep_time} seconds (Attempt {retries + 1}/{max_retries})...")
            retries += 1
            time.sleep(sleep_time)
    
    logger.critical("Could not connect to RabbitMQ after maximum retries. Exiting.")
    raise ConnectionError("Could not connect to RabbitMQ after maximum retries.")

def on_message(ch, method, properties, body):
    """Callback for processing messages."""
    trainer = ModelTrainer()
    
    try:
        payload = json.loads(body)
        model_id = payload.get('model_id')
        dataset_version = payload.get('dataset_version')
        
        if not model_id or not dataset_version:
            logger.error(f"Invalid message format: {payload}")
            # Identify as poison pill, nack without requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        logger.info(f"Received task: Retrain {model_id} (Data: {dataset_version})")
        
        # Execute Training
        result = trainer.train(model_id, dataset_version)
        
        if result:
            logger.info("Task successfully processed. Acknowledging message.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            logger.error(f"Training returned falsy value ({result!r}). Nacking message.")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except json.JSONDecodeError:
        logger.error(f"Failed to decode message body: {body}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        # Decide whether to requeue based on error type. 
        # For this task, strictly we nack(False) to avoid infinite loops if it's a code bug.
        # In a real system, we might requeue transient errors.
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def start_consuming(channel):
    # Ensure queue exists and is durable
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    # Fair dispatch: don't give a worker more than one message at a time
    channel.basic_qos(prefetch_count=1)
    
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_message)
    
    logger.info(' [*] Waiting for messages. To exit press CTRL+C')
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")
        channel.stop_consuming()
    except Exception as e:
        logger.critical(f"Worker crashed: {e}")

def main():
    connection = None
    try:
        connection = get_connection()
        channel = connection.channel()
        start_consuming(channel)
    except Exception as e:
        logger.exception(f"Fatal error in consumer: {e}")
        # Allow Docker to restart
        sys.exit(1)
    finally:
        if connection and not connection.is_closed:
            try:
                connection.close()
                logger.info("RabbitMQ connection closed.")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")

if __name__ == '__main__':
    main()
