import unittest
import requests
import time
import subprocess
import os
import pytest

@pytest.mark.integration
class TestE2E(unittest.TestCase):
    API_URL = "http://localhost:5000"

    def test_health_check(self):
        """Verify API is healthy and reachable."""
        try:
            response = requests.get(f"{self.API_URL}/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['status'], 'healthy')
        except requests.exceptions.ConnectionError:
            self.fail("API is not reachable. Ensure docker compose is running.")

    def test_trigger_retraining_flow(self):
        """
        Verify end-to-end flow:
        1. Trigger retraining via API.
        2. Verify API response.
        3. Check worker logs for confirmation.
        """
        payload = {
            "model_id": "e2e_test_model",
            "dataset_version": "v_integration"
        }
        
        # 1. Trigger API
        response = requests.post(f"{self.API_URL}/trigger-retraining", json=payload)
        self.assertEqual(response.status_code, 202)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        
        # 2. Check Logs (allow time for processing)
        time.sleep(5) 
        
        # We use docker compose logs to check for the specific log message
        # This assumes the test is running on the host where docker is available
        result = subprocess.run(
            ['docker', 'compose', 'logs', 'retraining_worker'],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout
        expected_log_part = f"Training completed. Model: e2e_test_model"
        
        if expected_log_part not in logs:
            # Fallback: maybe it's still processing? Wait a bit more
            time.sleep(5)
            result = subprocess.run(
                ['docker', 'compose', 'logs', 'retraining_worker'],
                capture_output=True,
                text=True
            )
            logs = result.stdout
            
        self.assertIn(expected_log_part, logs, "Worker logs did not contain confirmation of training.")

if __name__ == '__main__':
    unittest.main()
