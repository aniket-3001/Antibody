import asyncio
import logging
from memory_core.providers.mode_a import ModeAProvider

logging.basicConfig(level=logging.DEBUG)

async def test_ingest():
    print("Initializing provider...")
    provider = ModeAProvider()
    
    print("Testing document ingestion...")
    doc = "Transformers are better than RNNs for NLP tasks because they handle long-range dependencies using self-attention."
    
    try:
        source_id = await provider.remember(doc, title="NLP Note")
        print(f"Ingestion successful! Source ID: {source_id}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error during ingestion: {e}")
        print(f"Error during ingestion: {e}")

if __name__ == "__main__":
    asyncio.run(test_ingest())
