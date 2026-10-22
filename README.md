# Slothstep

Describe a task you keep putting off and get three tiny, realistic steps. The first one takes two minutes or less.

Built with Dash + dash-mantine-components and an open-weight model (Gemma 3) served by Ollama.

## Run locally

```
ollama pull gemma3:4b
pip install -r requirements.txt
python app.py
```

Set `OLLAMA_MODEL` and `OLLAMA_URL` to change the model or server.




## Free hosting

Render's free web service cannot run a model, so point it at a hosted open-weight model instead. Set
`LLM_BASE_URL` (e.g. `https://api.groq.com/openai/v1`), `LLM_API_KEY` and `OLLAMA_MODEL` (the model id) on the service.

## Demo mode

Set `DEMO_MODE=true` to serve canned plans without any model (no Ollama needed, works on a free host).
