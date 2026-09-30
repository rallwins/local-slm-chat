# Local SLM Chat

A small web chat interface for running language models locally through Ollama. FastAPI serves the frontend and proxies model listing and streaming chat requests to Ollama.

## Requirements

- Python
- [Ollama](https://ollama.com/download) installed and running

Ollama must be reachable at `http://localhost:11434`.

## Setup

Create and activate a virtual environment, then install the Python dependencies:

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

From the project root, start the application with:

```sh
python -m uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. The model selector lists the models available in Ollama.

## API

- `GET /api/models` returns the names of locally available Ollama models.
- `POST /api/chat` streams a chat response as plain text. The JSON body contains a `model` name and a `messages` array of `{ "role", "content" }` objects.

The Ollama address is currently configured in `app/ollama.py`.
