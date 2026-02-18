import unittest
from unittest.mock import patch, MagicMock
from app.main import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.main.get_publisher')
    def test_trigger_retraining_success(self, mock_get_publisher):
        """Test successful retraining trigger."""
        mock_publisher = MagicMock()
        mock_publisher.publish.return_value = True
        mock_get_publisher.return_value = mock_publisher
        
        payload = {"model_id": "m1", "dataset_version": "v1"}
        response = self.app.post('/trigger-retraining', json=payload)
        
        self.assertEqual(response.status_code, 202)
        self.assertIn("Retraining triggered successfully", response.get_json()['message'])

    def test_trigger_retraining_invalid_payload(self):
        """Test triggering with missing fields."""
        payload = {"model_id": "m1"} # Missing dataset_version
        response = self.app.post('/trigger-retraining', json=payload)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid payload", response.get_json()['error'])

    @patch('app.main.get_publisher')
    def test_trigger_retraining_service_unavailable(self, mock_get_publisher):
        """Test 503 when publisher unavailable."""
        mock_get_publisher.return_value = None
        
        payload = {"model_id": "m1", "dataset_version": "v1"}
        response = self.app.post('/trigger-retraining', json=payload)
        
        self.assertEqual(response.status_code, 503)

    @patch('app.main.get_publisher')
    def test_trigger_retraining_publish_fail(self, mock_get_publisher):
        """Test 500 when publish fails."""
        mock_publisher = MagicMock()
        mock_publisher.publish.return_value = False
        mock_get_publisher.return_value = mock_publisher

        payload = {"model_id": "m1", "dataset_version": "v1"}
        response = self.app.post('/trigger-retraining', json=payload)

        self.assertEqual(response.status_code, 500)

if __name__ == '__main__':
    unittest.main()
