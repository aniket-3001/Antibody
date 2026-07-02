import httpx

r = httpx.get("http://127.0.0.1:8000/api/v1/graph")
if r.status_code == 200:
    nodes = r.json().get("nodes", [])
    edges = r.json().get("edges", [])
    print(f"Graph has {len(nodes)} nodes and {len(edges)} edges.")
else:
    print(f"Failed to fetch graph: {r.status_code}")
