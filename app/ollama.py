import httpx


OLLAMA_URL = "http://localhost:11434"


async def get_models():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=30
        )

        response.raise_for_status()

        return response.json()


async def chat_stream(model: str, messages: list[dict]):
    async with httpx.AsyncClient(timeout=None) as client:

        async with client.stream(
            "POST",
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": True
            }
        ) as response:

            response.raise_for_status()

            async for line in response.aiter_lines():

                if line:
                    yield line