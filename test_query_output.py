import asyncio
import uuid
import json
from memory_core.config import get_provider

async def main():
    provider = get_provider()
    dataset = "demo"
    query = "What does the Transformer architecture improve over RNNs?"
    
    # 1. Test query (answers)
    answers = await provider.query(query, dataset=dataset, strategy="factual")
    print("Answers dict:")
    print(answers.answer)

asyncio.run(main())
