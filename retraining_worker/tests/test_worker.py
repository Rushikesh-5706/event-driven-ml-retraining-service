import unittest
from unittest.mock import MagicMock, patch
import json
from worker.model_trainer import ModelTrainer
from worker.consumer import on_message

class TestModelTrainer(unittest.TestCase):
    def test_train_success(self):
        trainer = ModelTrainer()
        # Mocking internal methods to avoid file I/O during unit test if needed,
        # but since we generate dummy data on fly if missing, strictly unit testing the logic is fine.
        # However, making it faster by mocking sleep and data load.
        with patch('time.sleep', return_value=None): 
            result = trainer.train("test_model", "v1")
            
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'success')
        self.assertIn('accuracy', result)

class TestConsumer(unittest.TestCase):
    @patch('worker.consumer.ModelTrainer')
    def test_on_message_success(self, MockTrainer):
        # Setup
        mock_ch = MagicMock()
        mock_method = MagicMock()
        mock_properties = MagicMock()
        body = json.dumps({"model_id": "m1", "dataset_version": "d1"}).encode()
        
        mock_trainer_instance = MockTrainer.return_value
        mock_trainer_instance.train.return_value = {"status": "success"}

        # Execute
        on_message(mock_ch, mock_method, mock_properties, body)

        # Assert
        mock_trainer_instance.train.assert_called_with("m1", "d1")
        mock_ch.basic_ack.assert_called_once()
        mock_ch.basic_nack.assert_not_called()

    def test_on_message_invalid_json(self):
        mock_ch = MagicMock()
        mock_method = MagicMock()
        body = b"invalid jso"

        on_message(mock_ch, mock_method, None, body)

        mock_ch.basic_nack.assert_called_with(delivery_tag=mock_method.delivery_tag, requeue=False)

if __name__ == '__main__':
    unittest.main()
