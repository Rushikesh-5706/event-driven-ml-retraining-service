from flask import Flask, request, jsonify
import os
import logging
import sys
from .services.message_publisher import MessagePublisher

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
        return str(log_record) # Ideally use json.dumps, but str representation is sufficient for this format demo

logging.basicConfig(level=logging.INFO)
root_logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
root_logger.addHandler(handler)
# Remove default handlers to avoid duplicate logs
for h in root_logger.handlers[:-1]:
    root_logger.removeHandler(h)

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Config
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')

publisher = None

def get_publisher():
    """Lazy instantiation of the publisher."""
    global publisher
    if publisher is None:
        try:
            publisher = MessagePublisher(RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS)
            # Pre-connect to fail fast if possible or just initialize state
        except Exception as e:
            logger.error(f"Failed to initialize publisher: {e}")
    return publisher

@app.route('/trigger-retraining', methods=['POST'])
def trigger_retraining():
    data = request.get_json()
    
    # Validation
    if not data:
        logger.warning("Received update request with empty body")
        return jsonify({"error": "Invalid payload", "details": "Request body must be JSON"}), 400
    
    model_id = data.get('model_id')
    dataset_version = data.get('dataset_version')
    
    if not model_id or not dataset_version:
        logger.warning(f"Validation failed for request: {data}")
        return jsonify({"error": "Invalid payload", "details": "Missing 'model_id' or 'dataset_version'"}), 400

    # Publish Event
    publisher_instance = get_publisher()
    if not publisher_instance:
         # Attempt to re-init
         publisher_instance = get_publisher()
         if not publisher_instance:
            return jsonify({"error": "Service Unavailable", "details": "Messaging service is down"}), 503

    success = publisher_instance.publish({
        "model_id": model_id,
        "dataset_version": dataset_version
    })

    if success:
        return jsonify({
            "status": "success", 
            "message": "Retraining triggered successfully",
            "model_id": model_id
        }), 202
    else:
        return jsonify({"error": "Internal Server Error", "details": "Failed to publish event"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    # Shallow health check
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
