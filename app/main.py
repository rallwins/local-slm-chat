import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.models import ChatRequest
from app.ollama import get_models, chat_stream


app = FastAPI(
    title="Local SLM Chat",
    version="1.0.0"
)


@app.get("/api/models")
async def models():

    result = await get_models()

    return {
        "models": [
            model["name"]
            for model in result.get("models", [])
        ]
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):

    messages = [
        {
            "role": message.role,
            "content": message.content
        }
        for message in request.messages
    ]

    async def generate():

        async for line in chat_stream(
            request.model,
            messages
        ):

            try:

                data = json.loads(line)

                if "message" in data:

                    content = data["message"].get(
                        "content",
                        ""
                    )

                    if content:
                        yield content

                if data.get("done"):
                    break

            except json.JSONDecodeError:
                continue

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )


app.mount(
    "/",
    StaticFiles(
        directory="static",
        html=True
    ),
    name="static"
)