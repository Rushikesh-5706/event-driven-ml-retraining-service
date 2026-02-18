import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from worker.model_trainer import ModelTrainer

class TestModelTrainer(unittest.TestCase):
    def setUp(self):
        self.trainer = ModelTrainer()

    @patch('worker.model_trainer.os.path.exists')
    @patch('worker.model_trainer.pd.read_csv')
    def test_load_data_success(self, mock_read_csv, mock_exists):
        """Test loading data from CSV."""
        mock_exists.return_value = True
        mock_df = pd.DataFrame({'feature_1': [1, 2], 'target': [0, 1]})
        mock_read_csv.return_value = mock_df
        
        self.trainer.dataset_path = "dummy_path.csv"
        # Call _load_data instead of load_data
        df = self.trainer._load_data()
        
        self.assertEqual(len(df), 2)

    @patch('worker.model_trainer.ModelTrainer._generate_dummy_data')
    def test_load_data_fallback(self, mock_gen_data):
        """Test fallback to dummy data."""
        mock_df = pd.DataFrame({'feature_1': [1, 2], 'target': [0, 1]})
        mock_gen_data.return_value = mock_df
        
        self.trainer.dataset_path = "non_existent.csv"
        df = self.trainer._load_data()
        
        self.assertEqual(len(df), 2)
        mock_gen_data.assert_called()

    @patch('worker.model_trainer.os.path.exists') # Added patch
    @patch('worker.model_trainer.pd.read_csv') # Added patch
    def test_train_success(self, mock_read_csv, mock_exists): # Modified parameters
        """Test successful training."""
        # Create a larger dummy dataset to ensure train_test_split works (need >1 sample in test set)
        data = {
            'feature1': np.random.rand(50),
            'feature2': np.random.rand(50),
            'target': np.random.randint(0, 2, 50)
        }
        df = pd.DataFrame(data)
        
        mock_read_csv.return_value = df
        mock_exists.return_value = True

        self.trainer.dataset_path = "dummy_path.csv" # Added to ensure _load_data is called
        result = self.trainer.train("test_model", "v1") # Modified model name
        
        self.assertTrue(result)
        self.assertEqual(result['status'], 'success')
        self.assertIn('accuracy', result) # Added assertion
        self.assertGreaterEqual(result['accuracy'], 0.0) # Added assertion

    def test_train_failure(self):
        """Test training failure handling."""
        # Force an error by invalid mocking or state
        with patch('worker.model_trainer.ModelTrainer._load_data', side_effect=Exception("Data Error")):
             result = self.trainer.train("m1", "v1")
             self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
