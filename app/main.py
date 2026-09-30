import json
import time
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.logger import get_logs, log_event
from app.metrics import (
    calculate_stats,
    calculate_tokens_per_second
)
from app.models import (
    ChatRequest,
    HealthResponse,
    ModelsResponse,
    PromptTemplatesResponse
)
from app.ollama import (
    chat_stream,
    get_models
)
from app.prompts import (
    get_prompt_template,
    get_template_list
)

app = FastAPI(
    title="Local SLM Chat",
    description=(
        "Local ChatGPT-like application "
        "powered by Ollama"
    ),
    version="1.0.0"
)


# --------------------------------------------------
# Health
# --------------------------------------------------

@app.get(
    "/api/health",
    response_model=HealthResponse
)
async def health():

    try:

        await get_models()

        return {
            "status": "healthy"
        }

    except Exception:

        raise HTTPException(
            status_code=503,
            detail="Ollama is unavailable"
        )


# --------------------------------------------------
# Models
# --------------------------------------------------

@app.get(
    "/api/models",
    response_model=ModelsResponse
)
async def models():

    try:

        model_list = await get_models()

        return {
            "models": model_list
        }

    except Exception as exc:

        raise HTTPException(
            status_code=503,
            detail=f"Unable to connect to Ollama: {exc}"
        )

# --------------------------------------------------
# Prompt Templates
# --------------------------------------------------
@app.get(
    "/api/prompts",
    response_model=PromptTemplatesResponse
)
async def prompts():

    return {
        "templates": get_template_list()
    }

# --------------------------------------------------
# Chat
# --------------------------------------------------

@app.post("/api/chat")
async def chat(request: ChatRequest):

    request_id = str(uuid.uuid4())

    start_time = time.perf_counter()

    first_token_time = None

    prompt_tokens = None

    output_tokens = None

    eval_duration_ns = None

    prompt_eval_duration_ns = None

    # ------------------------------------------
    # Get prompt template
    # ------------------------------------------

    template = get_prompt_template(
        request.prompt_template
    )
    # ------------------------------------------
    # Build messages
    # ------------------------------------------

    messages = [
        {
            "role": "system",
            "content": template.system_prompt
        }
    ]

    messages.extend(
        {
            "role": message.role,
            "content": message.content
        }
        for message in request.messages
    )

    async def generate():

        nonlocal first_token_time
        nonlocal prompt_tokens
        nonlocal output_tokens
        nonlocal eval_duration_ns
        nonlocal prompt_eval_duration_ns

        try:

            async for data in chat_stream(
                request.model,
                messages
            ):

                # ----------------------------------
                # Stream generated content
                # ----------------------------------

                message = data.get(
                    "message",
                    {}
                )

                content = message.get(
                    "content",
                    ""
                )

                if content:

                    if first_token_time is None:

                        first_token_time = (
                            time.perf_counter()
                        )

                    yield (
                        "event: token\n"
                        f"data: {json.dumps(content)}\n\n"
                    )

                # ----------------------------------
                # Final Ollama metrics
                # ----------------------------------

                if data.get("done"):

                    prompt_tokens = data.get(
                        "prompt_eval_count"
                    )

                    output_tokens = data.get(
                        "eval_count"
                    )

                    eval_duration_ns = data.get(
                        "eval_duration"
                    )

                    prompt_eval_duration_ns = (
                        data.get(
                            "prompt_eval_duration"
                        )
                    )

                    break

            # --------------------------------------
            # Calculate timing
            # --------------------------------------

            end_time = time.perf_counter()

            total_latency_ms = (
                end_time - start_time
            ) * 1000

            if first_token_time is not None:

                ttft_ms = (
                    first_token_time -
                    start_time
                ) * 1000

            else:

                ttft_ms = None

            tokens_per_second = (
                calculate_tokens_per_second(
                    output_tokens,
                    eval_duration_ns
                )
            )

            generation_time_ms = None

            if eval_duration_ns:

                generation_time_ms = (
                    eval_duration_ns /
                    1_000_000
                )

            # --------------------------------------
            # Log
            # --------------------------------------

            log_event({

                "event": "chat_completion",

                "request_id": request_id,

                "model": request.model,

                "prompt_template":
                        request.prompt_template,

                "message_count": len(
                    messages
                ),

                "prompt_tokens": (
                    prompt_tokens
                ),

                "output_tokens": (
                    output_tokens
                ),

                "prompt_eval_duration_ms": (
                    prompt_eval_duration_ns /
                    1_000_000
                    if prompt_eval_duration_ns
                    else None
                ),

                "generation_time_ms": (
                    generation_time_ms
                ),

                "time_to_first_token_ms": (
                    ttft_ms
                ),

                "total_latency_ms": (
                    total_latency_ms
                ),

                "tokens_per_second": (
                    tokens_per_second
                ),

                "status": "success"
            })

            # --------------------------------------
            # Send metrics to browser
            # --------------------------------------

            metrics = {

                "request_id":
                    request_id,

                "model":
                    request.model,

                "prompt_template":
                    request.prompt_template,

                "prompt_tokens":
                    prompt_tokens,

                "output_tokens":
                    output_tokens,

                "prompt_eval_duration_ms": (
                    prompt_eval_duration_ns /
                    1_000_000
                    if prompt_eval_duration_ns
                    else None
                ),

                "generation_time_ms":
                    generation_time_ms,

                "time_to_first_token_ms":
                    ttft_ms,

                "total_latency_ms":
                    total_latency_ms,

                "tokens_per_second":
                    tokens_per_second
            }

            yield (
                "event: metrics\n"
                f"data: {json.dumps(metrics)}\n\n"
            )

            yield (
                "event: done\n"
                "data: {}\n\n"
            )

        except Exception as exc:

            log_event({

                "event": "chat_completion",

                "request_id":
                    request_id,

                "model":
                    request.model,

                "message_count":
                    len(messages),

                "status":
                    "error",

                "error":
                    str(exc)
            })

            error_data = {
                "request_id":
                    request_id,

                "error":
                    str(exc)
            }

            yield (
                "event: error\n"
                f"data: {json.dumps(error_data)}\n\n"
            )

    return StreamingResponse(

        generate(),

        media_type="text/event-stream",

        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-ID": request_id
        }
    )


# --------------------------------------------------
# Logs
# --------------------------------------------------

@app.get("/api/logs")
async def logs(limit: int = 100):

    limit = max(
        1,
        min(limit, 1000)
    )

    return {
        "logs": get_logs(limit)
    }


# --------------------------------------------------
# Statistics
# --------------------------------------------------

@app.get("/api/stats")
async def stats():

    logs = get_logs(10000)

    return calculate_stats(logs)


# --------------------------------------------------
# Frontend
# --------------------------------------------------

app.mount(
    "/",
    StaticFiles(
        directory="static",
        html=True
    ),
    name="static"
)