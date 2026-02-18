import unittest
from unittest.mock import patch, MagicMock
from app.main import app
from app.services.message_publisher import MessagePublisher

class TestTrainingTriggerAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.main.get_publisher')
    def test_trigger_retraining_success(self, mock_get_publisher):
        # Mock publisher instance
        mock_publisher_instance = MagicMock()
        mock_publisher_instance.publish.return_value = True
        mock_get_publisher.return_value = mock_publisher_instance

        payload = {"model_id": "model_v1", "dataset_version": "v1.0"}
        response = self.app.post('/trigger-retraining', json=payload)
        
        self.assertEqual(response.status_code, 202)
        self.assertIn("Retraining triggered successfully", response.get_json()['message'])

    def test_trigger_retraining_invalid_payload(self):
        payload = {"model_id": "model_v1"} # Missing dataset_version
        response = self.app.post('/trigger-retraining', json=payload)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing 'model_id' or 'dataset_version'", response.get_json()['details'])

    @patch('app.services.message_publisher.pika.BlockingConnection')
    def test_publisher_connection(self, mock_pika_connection):
        # Setup mock connection and channel
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika_connection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        
        publisher = MessagePublisher("host", 5672, "user", "pass", retry_delay=0)
        result = publisher.publish({"test": "data"})
        
        self.assertTrue(result)
        mock_channel.basic_publish.assert_called_once()
        mock_channel.queue_declare.assert_called_with(queue='retraining_queue', durable=True)

if __name__ == '__main__':
    unittest.main()
