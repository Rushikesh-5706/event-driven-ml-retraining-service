import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import logging
import time
import os

logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self, dataset_path='/app/data/dummy_dataset.csv'):
        self.dataset_path = dataset_path
        self.model = None

    def _load_data(self):
        """Loads dataset from CSV. Generates dummy data if file is missing (failsafe)."""
        if not os.path.exists(self.dataset_path):
            logger.warning(f"Dataset path {self.dataset_path} not found. Generating in-memory dummy data.")
            return self._generate_dummy_data()
        
        try:
            return pd.read_csv(self.dataset_path)
        except Exception as e:
            logger.error(f"Failed to read CSV: {e}")
            raise

    def _generate_dummy_data(self):
        np.random.seed(42)
        data = {f'feature_{i}': np.random.rand(100) * 10 for i in range(3)}
        data['target'] = np.random.randint(0, 2, 100)
        return pd.DataFrame(data)

    def train(self, model_id, dataset_version):
        """
        Simulates training a model.
        Returns: Dict with training metadata or None on failure.
        """
        logger.info(f"Starting training for model {model_id} on version {dataset_version}...")
        
        try:
            # Simulate heavy workload
            time.sleep(2) 

            df = self._load_data()
            X = df.drop('target', axis=1)
            y = df['target']
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            clf = LogisticRegression()
            clf.fit(X_train, y_train)
            
            predictions = clf.predict(X_test)
            accuracy = accuracy_score(y_test, predictions)
            
            logger.info(f"Training completed. Model: {model_id}, Accuracy: {accuracy:.4f}")
            
            return {
                "model_id": model_id,
                "dataset_version": dataset_version,
                "accuracy": accuracy,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Training failed for {model_id}: {e}")
            raise
