import requests
url = "http://localhost:8000/api/v1/recall"
data = {"query": "yolo"}
print("Sending request...")
response = requests.post(url, json=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
