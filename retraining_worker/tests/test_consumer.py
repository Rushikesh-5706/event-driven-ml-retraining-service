import unittest
from unittest.mock import MagicMock, patch
import json
from worker.consumer import on_message

class TestConsumer(unittest.TestCase):
    @patch('worker.consumer.ModelTrainer')
    def test_on_message_success(self, mock_trainer_cls):
        """Test successful message processing."""
        mock_trainer = mock_trainer_cls.return_value
        mock_trainer.train.return_value = True
        
        mock_ch = MagicMock()
        method = MagicMock()
        method.delivery_tag = 1
        body = json.dumps({"model_id": "m1", "dataset_version": "v1"}).encode('utf-8')
        
        on_message(mock_ch, method, None, body)
        
        mock_trainer.train.assert_called_with("m1", "v1")
        mock_ch.basic_ack.assert_called_with(delivery_tag=1)

    @patch('worker.consumer.ModelTrainer')
    def test_on_message_failure(self, mock_trainer_cls):
        """Test message processing failure (training fails)."""
        mock_trainer = mock_trainer_cls.return_value
        mock_trainer.train.return_value = False
        
        mock_ch = MagicMock()
        method = MagicMock()
        method.delivery_tag = 1
        body = json.dumps({"model_id": "m1", "dataset_version": "v1"}).encode('utf-8')
        
        on_message(mock_ch, method, None, body)
        
        mock_ch.basic_nack.assert_called_with(delivery_tag=1, requeue=False)

    def test_on_message_invalid_json(self):
        """Test handling of invalid JSON."""
        mock_ch = MagicMock()
        method = MagicMock()
        method.delivery_tag = 1
        body = b"invalid json"
        
        on_message(mock_ch, method, None, body)
        
        mock_ch.basic_nack.assert_called_with(delivery_tag=1, requeue=False)

if __name__ == '__main__':
    unittest.main()
