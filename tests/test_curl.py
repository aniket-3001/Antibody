import os
import httpx
import json

api_key = os.getenv("LLM_API_KEY")
url = "https://integrate.api.nvidia.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "meta/llama-3.3-70b-instruct",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 100
}

try:
    r = httpx.post(url, headers=headers, json=payload, timeout=10.0)
    print(r.status_code)
    print(r.text)
except Exception as e:
    print(f"Error: {e}")
