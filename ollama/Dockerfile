FROM ollama/ollama:latest
ENV OLLAMA_HOST=0.0.0.0:11434 OLLAMA_MODEL=gemma3:1b
EXPOSE 11434
ENTRYPOINT ["/bin/sh", "-c", "ollama serve & until ollama list >/dev/null 2>&1; do sleep 1; done; ollama pull $OLLAMA_MODEL; wait"]
