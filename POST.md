---
title: Slothstep: a lazy-friendly app that turns "ugh, I'll do it later" into three tiny steps
published: false
tags: devchallenge, hf26challenge, hacktoberfest, productivity
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge: Week 3 – Slow and Steady](https://dev.to/challenges/hacktoberfest).*

## What I Built

**Slothstep** is a tiny web app for the thing sloths do best: not panicking.

You type whatever you keep putting off ("clean the whole flat before Saturday", "write that difficult email to my boss", "sort the files on my laptop") and an open-weight model answers with exactly **three steps**:

1. one you can start *right now* and finish in two minutes or less,
2. one that follows naturally,
3. one that finishes the job.

Every step has a realistic time estimate, and you can tick them off as you go. The point is not a perfect plan. The point is that the first step is so small there is no excuse left not to start.

**The effort it saves:** the hardest part of a dreaded task is rarely the task, it is the staring. Slothstep replaces "where do I even begin?" with one concrete, two-minute action. (On my machine a plan takes about 25 seconds to generate with a 4B model.)

## Demo

- Live app (demo mode with sample plans, because a free host cannot run a model): https://slothstep.onrender.com
- Real thing: clone the repo, `ollama pull gemma3:4b`, `pip install -r requirements.txt`, `python app.py`
- Code: {% embed https://github.com/banana0000/slothstep %}

<!-- Add a screenshot or GIF here before publishing: ![Slothstep screenshot](IMAGE_URL) -->

The free host may take about a minute to wake up on the first visit.

## How I Built It

- **UI:** [Dash](https://dash.plotly.com/) with [Dash Mantine Components](https://www.dash-mantine-components.com/) (light and dark mode), a single Python file.
- **Model:** [Gemma 3](https://ai.google.dev/gemma) (4B) running locally through [Ollama](https://ollama.com/). The same code can also talk to any OpenAI-compatible host serving an open-weight model. The free hosted demo runs in a clearly labelled demo mode with sample plans, since a free host cannot run a model.
- **Reliable output:** the model is asked for JSON only, then the app validates it (exactly three steps, non-empty text, positive integer minutes) and shows a friendly error instead of garbage if the model misbehaves.
- **Prompting:** low temperature, a hard limit of two minutes for step one, and an explicit "do not invent missing details" instruction so it doesn't hallucinate a kitchen you don't have.
- **Deploy:** a `render.yaml` Blueprint with a web service and a private Ollama service. The Ollama service needs a paid instance, so the free demo runs with `DEMO_MODE=true`.

## Why Open Innovation Matters Here

What people procrastinate on is personal: unanswered emails, messy folders, awkward conversations. I don't want those sent to a closed API.

- **Private by default:** run it locally and your to-dos never leave your machine.
- **Works offline:** no internet, no problem. Ollama and a 4B model are enough.
- **Set up once, free forever:** no subscription, no per-token bill for something you use ten times a week.
- **Swappable:** because Slothstep speaks both Ollama and the OpenAI-compatible API, moving from a local Gemma to a hosted open-weight model is two environment variables, not a rewrite.

A closed model might write slightly nicer sentences. But for a three-line plan, a small open model is more than good enough, and I keep control of my data.

## Prize Categories

- **Best Use of Gemma:** Gemma 3 is the model at the core of the app.
- **Best Use of Render:** the app is deployed from a `render.yaml` Blueprint.

Thanks for reading, and please take it slow. 🦥
