import asyncio
import time
from memory_core.config import get_provider

async def main():
    provider = get_provider()
    dataset = "demo"
    query = "What does the Transformer architecture improve over RNNs?"
    
    # 1. Test query (answers)
    t0 = time.perf_counter()
    answers = await provider.query(query, dataset=dataset, strategy="factual")
    t1 = time.perf_counter()
    print(f"provider.query took: {t1-t0:.2f}s")
    
    # 2. Test fetch_graph
    t0 = time.perf_counter()
    graph = await provider.fetch_graph(dataset=dataset)
    t1 = time.perf_counter()
    print(f"fetch_graph took: {t1-t0:.2f}s")

asyncio.run(main())
