import httpx
import json
import time

BASE = "http://127.0.0.1:8000/api/v1"

def test_all():
    with httpx.Client(timeout=300.0) as client:
        print("1. Testing /health")
        r = client.get(f"{BASE}/health")
        print(f"Health: {r.status_code} - {r.text}")
        assert r.status_code == 200

        print("\n2. Testing /remember")
        doc = "Transformers are better than RNNs for NLP tasks because they handle long-range dependencies using self-attention."
        r = client.post(
            f"{BASE}/remember",
            data={
                "content_type": "text",
                "content": doc,
                "title": "NLP Note",
            }
        )
        print(f"Remember: {r.status_code} - {r.text}")
        assert r.status_code == 200
        source_id = r.json().get("source_id")

        print("\n3. Testing /sources")
        r = client.get(f"{BASE}/sources")
        print(f"Sources: {r.status_code} - {r.text}")
        assert r.status_code == 200

        print("\n4. Testing /graph")
        r = client.get(f"{BASE}/graph")
        print(f"Graph: {r.status_code} - {len(r.json().get('nodes', []))} nodes")
        assert r.status_code == 200

        print("\n5. Testing /improve")
        r = client.post(
            f"{BASE}/improve",
            data={
                "content_type": "text",
                "content": "Transformers use multi-head attention.",
                "title": "NLP Note Addendum",
            }
        )
        print(f"Improve: {r.status_code} - {r.text}")
        assert r.status_code == 200
        improve_source_id = r.json().get("source_id")

        print("\n6. Testing /recall")
        r = client.post(
            f"{BASE}/recall",
            json={"query": "What do transformers use for attention?", "strategy": "factual"}
        )
        print(f"Recall: {r.status_code} - {r.text}")
        assert r.status_code == 200

        print("\n7. Testing /stats")
        r = client.get(f"{BASE}/stats")
        print(f"Stats: {r.status_code} - {r.text}")
        assert r.status_code == 200

        print("\n8. Testing /forget")
        if improve_source_id:
            r = client.delete(f"{BASE}/forget/{improve_source_id}")
            print(f"Forget: {r.status_code} - {r.text}")
            assert r.status_code == 200

    print("\n✅ All APIs tested successfully!")

if __name__ == "__main__":
    test_all()
