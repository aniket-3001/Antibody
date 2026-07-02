import os
import litellm
import asyncio

litellm.set_verbose = True

async def test_nim():
    print("Testing litellm with NIM Custom Base...")
    try:
        response = await litellm.acompletion(
            model="openai/meta/llama-3.3-70b-instruct",
            api_base="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv("LLM_API_KEY"),
            messages=[{"role": "user", "content": "Hello, how are you?"}]
        )
        print("Success!")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(test_nim())
