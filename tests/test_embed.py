import os
import httpx

api_key = os.getenv("LLM_API_KEY")
url = "https://integrate.api.nvidia.com/v1/embeddings"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "nvidia/nv-embedqa-e5-v5",
    "input": ["Hello"],
    "input_type": "query"
}

try:
    r = httpx.post(url, headers=headers, json=payload, timeout=10.0)
    print(r.status_code)
    print("Success")
except Exception as e:
    print(f"Error: {e}")
