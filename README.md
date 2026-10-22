# Slothstep

Describe a task you keep putting off and get three tiny, realistic steps. The first one takes two minutes or less.

Built with Dash + dash-bootstrap-components and an open-weight model (Gemma 3) served by Ollama.

## Run locally

```
ollama pull gemma3:4b
pip install -r requirements.txt
python app.py
```

Set `OLLAMA_MODEL` and `OLLAMA_URL` to change the model or server.

## Deploy

`render.yaml` defines a web service plus a private Ollama service (Render Blueprint).
