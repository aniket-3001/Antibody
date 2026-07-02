import asyncio
import os
import litellm

os.environ["OPENAI_API_KEY"] = "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"

async def test_embedding():
    try:
        print("Testing passage...")
        res1 = await litellm.aembedding(
            model="openai/nvidia/nv-embedqa-e5-v5",
            input=["This is a test document."],
            api_base="https://integrate.api.nvidia.com/v1",
            input_type="passage"
        )
        print("Passage OK")
    except Exception as e:
        print(f"Passage failed: {e}")

    try:
        print("Testing query...")
        res2 = await litellm.aembedding(
            model="openai/nvidia/nv-embedqa-e5-v5",
            input=["What is the test document about?"],
            api_base="https://integrate.api.nvidia.com/v1",
            input_type="query"
        )
        print("Query OK")
    except Exception as e:
        print(f"Query failed: {e}")

asyncio.run(test_embedding())
