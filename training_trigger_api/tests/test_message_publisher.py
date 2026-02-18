import unittest
from unittest.mock import MagicMock, patch
from app.services.message_publisher import MessagePublisher

class TestMessagePublisher(unittest.TestCase):
    @patch('app.services.message_publisher.pika.BlockingConnection')
    def test_connect_success(self, mock_connection):
        """Test successful connection."""
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        
        # Initialize publisher
        publisher = MessagePublisher('host', 5672, 'user', 'pass')
        
        # Call connect explicitly
        publisher._connect()
        
        # Verify connection established
        mock_connection.assert_called()
        self.assertIsNotNone(publisher._channel)
        
    @patch('app.services.message_publisher.pika.BlockingConnection')
    def test_publish_success(self, mock_connection):
        """Test successful message publishing."""
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        
        publisher = MessagePublisher('host', 5672, 'user', 'pass')
        message = {"key": "value"}
        
        result = publisher.publish(message)
        
        self.assertTrue(result)
        # Verify queue_declare called during connect
        mock_channel.queue_declare.assert_called_with(queue='retraining_queue', durable=True)
        # Verify basic_publish called
        mock_channel.basic_publish.assert_called()

    @patch('app.services.message_publisher.pika.BlockingConnection')
    def test_publish_failure(self, mock_connection):
        """Test publishing when connection fails."""
        mock_channel = MagicMock()
        # Mock publish to raise exception
        mock_channel.basic_publish.side_effect = Exception("Connection lost")
        mock_connection.return_value.channel.return_value = mock_channel
        
        publisher = MessagePublisher('host', 5672, 'user', 'pass')
        result = publisher.publish({"key": "value"})
        
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
