import pika
import logging
import time
import json
from pika.exceptions import AMQPConnectionError, AMQPChannelError

logger = logging.getLogger(__name__)

class MessagePublisher:
    def __init__(self, host, port, user, password, queue_name='retraining_queue', max_retries=5, retry_delay=5):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.queue_name = queue_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.credentials = pika.PlainCredentials(self.user, self.password)
        self.connection_params = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=self.credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        self._connection = None
        self._channel = None

    def _connect(self):
        """Establish connection to RabbitMQ with retry logic."""
        if self._connection and not self._connection.is_closed:
            return

        retries = 0
        while retries < self.max_retries:
            try:
                logger.info(f"Connecting to RabbitMQ at {self.host}:{self.port}...")
                self._connection = pika.BlockingConnection(self.connection_params)
                self._channel = self._connection.channel()
                # Declare the queue as durable
                self._channel.queue_declare(queue=self.queue_name, durable=True)
                logger.info("Successfully connected to RabbitMQ.")
                return
            except AMQPConnectionError as e:
                retries += 1
                logger.warning(f"Connection attempt {retries} failed: {e}. Retrying in {self.retry_delay}s...")
                time.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"Unexpected error during connection: {e}")
                raise

        raise ConnectionError(f"Failed to connect to RabbitMQ after {self.max_retries} attempts.")

    def publish(self, message: dict) -> bool:
        """
        Publishes a message to the RabbitMQ queue.
        Returns True if successful, False otherwise.
        """
        try:
            self._connect()
            
            properties = pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type='application/json'
            )
            
            self._channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=json.dumps(message),
                properties=properties
            )
            
            logger.info(f"Published message to {self.queue_name}: {message}")
            return True
            
        except (pika.exceptions.AMQPError, IOError) as e:
            logger.error(f"Failed to publish message: {e}")
            # Reset connection state to force full reconnect next time
            if self._connection:
                try:
                    self._connection.close()
                except Exception:
                    pass # Ignore errors during close if already in an error state
            self._connection = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error during publish: {e}")
            return False

    def close(self):
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            logger.info("RabbitMQ connection closed.")
