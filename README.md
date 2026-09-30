# Local SLM Chat

A local web chat interface for language models served by Ollama. FastAPI serves the frontend and proxies model discovery and streaming chat requests.

## Features

- Discover and select locally available Ollama models.
- Stream responses and stop generation from the chat interface.
- Check Ollama connection status and inspect per-request latency, time to first token (TTFT), token counts, and generation speed.
- Review recent requests and aggregate performance statistics in the Observability panel.

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                         USER                            │
│                                                         │
│             "Explain Spark architecture"                │
└───────────────────────┬─────────────────────────────────┘
						│
						▼
┌─────────────────────────────────────────────────────────┐
│                    WEB FRONTEND                         │
│               HTML + CSS + JavaScript                   │
│                                                         │
│  - Chat UI                                              │
│  - Model selector                                       │
│  - Prompt selector                                      │
│  - Streaming response                                   │
└───────────────────────┬─────────────────────────────────┘
						│
					HTTP / SSE
						│
						▼
┌─────────────────────────────────────────────────────────┐
│                       FASTAPI                           │
│                                                         │
│  /api/chat                                              │
│                                                         │
│  - Validate request                                     │
│  - Select prompt template                               │
│  - Build conversation                                   │
│  - Generate request ID                                  │
│  - Measure latency                                      │
│  - Stream response                                      │
│  - Record metrics                                       │
└───────────────────────┬─────────────────────────────────┘
						│
				  HTTP localhost
						│
						▼
┌─────────────────────────────────────────────────────────┐
│                       OLLAMA                            │
│                  localhost:11434                        │
│                                                         │
│            Model management + inference runtime         │
└───────────────────────┬─────────────────────────────────┘
						│
						▼
┌─────────────────────────────────────────────────────────┐
│                  LOCAL LLM MODEL                        │
│                                                         │
│              Llama / Qwen / Mistral / Gemma             │
│                                                         │
│                  Token generation                       │
└───────────────────────┬─────────────────────────────────┘
						│
				  Streaming tokens
						│
						▼
┌─────────────────────────────────────────────────────────┐
│                       FASTAPI                           │
│                                                         │
│  Calculate:                                             │
│  - TTFT                                                 │
│  - Generation time                                      │
│  - Total latency                                        │
│  - Tokens/sec                                           │
│  - Prompt tokens                                        │
│  - Output tokens                                        │
└───────────────────────┬─────────────────────────────────┘
						│
					SSE token stream
						│
						▼
┌─────────────────────────────────────────────────────────┐
│                    WEB FRONTEND                         │
│                                                         │
│        "Spark is a distributed..."                      │
│        "..."                                            │
│        "..."                                            │
└─────────────────────────────────────────────────────────┘

						│
						▼
				 logs/chat.jsonl
```

## Requirements

- Python 3.10 or newer
- [Ollama](https://ollama.com/download), running at `http://localhost:11434`

## Setup

Create and activate a virtual environment, then install the dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Download at least one model. For example:

```sh
ollama pull llama3.2
```

If Ollama is not already running, start it in a separate terminal:

```sh
ollama serve
```

## Run

From the project root, start the application:

```sh
python -m uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. The model selector lists installed Ollama models.

## API

- `GET /api/health` reports whether Ollama is reachable.
- `GET /api/models` returns the names of locally available models.
- `POST /api/chat` accepts a model and a non-empty `messages` array of `{ "role", "content" }` objects. It streams server-sent events named `token`, `metrics`, `done`, or `error`.
- `GET /api/logs?limit=100` returns recent request records. The limit is clamped to 1–1000.
- `GET /api/stats` returns aggregate statistics for up to the latest 10,000 records.

## Local Data

The application connects to Ollama at `localhost`; it does not use a cloud API. Request metadata (model, counts, timings, status, and error details for failed requests) is stored in `logs/chat.jsonl`. Prompt and response text are not written to this log. The `logs/` directory is ignored by Git.
