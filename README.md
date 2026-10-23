# 🦥 Slothstep

Describe a task you keep putting off and get **three tiny, realistic steps**. The first one takes two minutes or less, so there is no excuse left not to start.

Built for the Hacktoberfest Open-Source AI Challenge (Week 3: *Slow and Steady*) with an open-weight model ([Gemma 3](https://ai.google.dev/gemma)) served by [Ollama](https://ollama.com/).

**Live demo:** https://slothstep.onrender.com

## Features

- Three steps with time estimates, validated so the model cannot return malformed plans
- Tick steps off as you go
- Light and dark mode (remembered in the browser)
- A badge showing whether the model server is running
- Runs fully offline with a local model, or against any OpenAI-compatible host serving an open-weight model

Stack: [Dash](https://dash.plotly.com/) + [Dash Mantine Components](https://www.dash-mantine-components.com/), Python.

## Run locally

```
ollama pull gemma3:4b
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:8050.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_MODEL` | `gemma3:4b` | Model name (Ollama tag, or model id on a hosted API) |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server |
| `LLM_BASE_URL` | unset | OpenAI-compatible API base URL; if set, used instead of Ollama |
| `LLM_API_KEY` | unset | API key for `LLM_BASE_URL` |
| `DEMO_MODE` | `false` | Serve canned plans without any model (works on a free host) |
| `PORT` | `8050` | Port to listen on |

## Deploy on Render

`render.yaml` is a Blueprint for a free web service running in demo mode (`DEMO_MODE=true`, sample plans).
For a real model, add a private Ollama service built from `ollama/Dockerfile` (needs a paid instance, 2 GB RAM) and set `OLLAMA_URL`, or use the hosted option below.
To stay on the free tier, set `DEMO_MODE=true`, or point `LLM_BASE_URL` / `LLM_API_KEY` / `OLLAMA_MODEL` at a hosted open-weight model.
