import requests
import time

url = "http://localhost:8000/api/v1/recall"
data = {"query": "yolo"}

print("Sending POST request to /api/v1/recall...")
start = time.time()
try:
    response = requests.post(url, json=data, timeout=60)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except requests.exceptions.Timeout:
    print("Request timed out after 60 seconds!")
except Exception as e:
    print(f"Error: {e}")

print(f"Elapsed time: {time.time() - start:.2f} seconds")
