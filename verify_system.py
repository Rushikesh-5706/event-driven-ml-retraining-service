import requests
import time
import subprocess
import sys

API_URL = "http://localhost:5000"

def log(msg):
    print(f"[TEST] {msg}")

def check_health():
    try:
        resp = requests.get(f"{API_URL}/health")
        if resp.status_code == 200:
            log("API is healthy.")
            return True
    except Exception as e:
        log(f"API health check failed: {e}")
    return False

def trigger_retraining():
    payload = {"model_id": "e2e_model", "dataset_version": "v_e2e_1"}
    try:
        resp = requests.post(f"{API_URL}/trigger-retraining", json=payload)
        if resp.status_code == 202:
            log(f"Trigger success: {resp.json()}")
            return True
        else:
            log(f"Trigger failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        log(f"Trigger exception: {e}")
    return False

def check_worker_logs():
    log("Checking worker logs for processing confirmation...")
    # Give worker time to process
    time.sleep(5)
    
    try:
        result = subprocess.run(
            ["docker-compose", "logs", "retraining_worker"], 
            capture_output=True, text=True
        )
        logs = result.stdout
        if "Training completed. Model: e2e_model" in logs:
            log("Worker successfully processed the task!")
            return True
        else:
            log("Worker logs did not contain expected success message yet.")
            print("--- LOG DUMP ---")
            print(logs)
            print("----------------")
            return False
    except Exception as e:
        log(f"Failed to fetch logs: {e}")
        return False

def main():
    log("Starting E2E Verification...")
    
    # Wait for API to be ready
    retries = 10
    while retries > 0:
        if check_health():
            break
        time.sleep(2)
        retries -= 1
    
    if retries == 0:
        log("API never became healthy. Aborting.")
        sys.exit(1)

    if not trigger_retraining():
        sys.exit(1)

    if not check_worker_logs():
        sys.exit(1)

    log("E2E Verification PASSED!")

if __name__ == "__main__":
    main()
