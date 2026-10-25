"""Slothstep: turn an overwhelming to-do into three quick steps, with an open-weight model."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, dcc, html

MODEL = os.environ.get("OLLAMA_MODEL") or "gemma3:4b"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
# Optional: any OpenAI-compatible host serving an open-weight model (used instead of Ollama).
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "").rstrip("/")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
# Demo mode: canned plans, no model needed (e.g. on a free host).
DEMO_MODE = os.environ.get("DEMO_MODE", "").lower() in {"1", "true", "yes"}
EXAMPLES = [
    "I have to clean the whole flat because guests arrive on Saturday",
    "I need to write a long, difficult email to my boss",
    "I haven't sorted the files on my laptop in years",
]


DEMO_PLANS = {
    EXAMPLES[0]: [
        ("Pick up everything that is on the floor and put it on the sofa.", 2),
        ("Wipe the kitchen counter and clear the sink.", 10),
        ("Vacuum the main room and take out the trash.", 15),
    ],
    EXAMPLES[1]: [
        ("Write one sentence: what do you need from your boss?", 2),
        ("Add two or three bullet points of context, nothing more.", 5),
        ("Read it once out loud, fix the tone, and hit send.", 8),
    ],
    EXAMPLES[2]: [
        ("Create one folder called 'To sort' on your desktop.", 1),
        ("Drag everything that is lying around into it.", 5),
        ("Open it and sort just the first 10 files, then stop.", 10),
    ],
}
DEMO_DEFAULT = [
    ("Write the task down in one sentence.", 2),
    ("List the first three things it needs, in any order.", 5),
    ("Do the smallest one on that list.", 10),
]


def make_plan(task: str, model: str = MODEL, ollama_url: str = OLLAMA_URL) -> list[dict]:
    if DEMO_MODE:
        steps = DEMO_PLANS.get(task, DEMO_DEFAULT)
        return [{"action": a, "minutes": m} for a, m in steps]

    prompt = (
        "You are a practical everyday helper. The user describes a task they "
        "are procrastinating on. Break it into exactly 3 short steps to do "
        "in order. The first step must be startable right now and take at "
        "most 2 minutes. Keep time estimates realistic and do not invent "
        "missing details. Always write the steps in English, even if the task is in another language. Reply only in this JSON format: "
        '{"steps":[{"action":"concrete step","minutes":2},'
        '{"action":"next step","minutes":5},'
        '{"action":"final step","minutes":10}]}'
        f"\n\nTask: {task}"
    )
    if LLM_BASE_URL:
        endpoint = f"{LLM_BASE_URL}/chat/completions"
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}",
        }
    else:
        endpoint = f"{ollama_url.rstrip('/')}/api/chat"
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
        }
        headers = {"Content-Type": "application/json"}
    request = Request(
        endpoint, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST"
    )

    try:
        with urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
        message = result["choices"][0]["message"] if LLM_BASE_URL else result["message"]
        plan = json.loads(message["content"])["steps"]
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Ollama error ({exc.code}): {detail or exc.reason}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(
            "Cannot reach the model server. Check it is running and try again."
        ) from exc
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("The model did not return a valid plan.") from exc

    if (
        not isinstance(plan, list)
        or len(plan) != 3
        or any(
            not isinstance(step, dict)
            or not isinstance(step.get("action"), str)
            or not step["action"].strip()
            or not isinstance(step.get("minutes"), int)
            or isinstance(step.get("minutes"), bool)
            or step["minutes"] < 1
            for step in plan
        )
    ):
        raise RuntimeError("The model did not return exactly 3 valid steps.")
    return plan


def model_status() -> tuple[str, str]:
    """Return (badge colour, label) describing whether the model server is up."""
    if DEMO_MODE:
        return "warning", "Demo mode · sample plans, no model"
    if LLM_BASE_URL:
        url, name = f"{LLM_BASE_URL}/models", "Hosted model"
    else:
        url, name = f"{OLLAMA_URL.rstrip('/')}/api/tags", "Ollama"
    request = Request(url, headers={"Authorization": f"Bearer {LLM_API_KEY}"})
    try:
        with urlopen(request, timeout=3):
            pass
    except HTTPError:
        pass  # the server answered, so it is up
    except (URLError, TimeoutError, OSError):
        return "danger", f"{name} is not running"
    return "success", f"{name} is running · {MODEL}"


GRADIENT = {"from": "pink", "to": "blue", "deg": 90}
GRADIENT_REV = {"from": "blue", "to": "pink", "deg": 90}


def step_card(index: int, step: dict) -> dmc.Paper:
    first = index == 1
    return dmc.Paper(
        dmc.Group(
            [
                dmc.ThemeIcon(
                    str(index),
                    size=52,
                    radius=0,
                    variant="gradient",
                    gradient=GRADIENT,
                    style={"fontSize": "1.3rem", "fontWeight": 700},
                ),
                dmc.Stack(
                    [
                        dmc.Group(
                            [
                                dmc.Checkbox(
                                    id={"type": "done", "index": index}, size="md", radius=0
                                ),
                                dmc.Text(
                                    step["action"],
                                    id={"type": "txt", "index": index},
                                    size="xl",
                                    fw=500,
                                ),
                            ],
                            wrap="nowrap",
                            align="flex-start",
                        ),
                        dmc.Text(
                            "Start here – this is all you need to do right now."
                            if first
                            else "Once the previous one is done.",
                            size="sm",
                            c="gray.4",
                            style={
                                "background": "#000",
                                "padding": "2px 10px",
                                "width": "fit-content",
                            },
                        ),
                    ],
                    gap=4,
                    style={"flex": 1},
                ),
                dmc.Badge(
                    f"~{step['minutes']} min",
                    size="xl",
                    radius=0,
                    variant="gradient" if first else "light",
                    gradient=GRADIENT,
                    color="blue",
                ),
            ],
            wrap="nowrap",
            align="center",
        ),
        withBorder=True,
        shadow="sm",
        radius=0,
        p="lg",
        className="step-card",
    )


app = dash.Dash(__name__, title="Slothstep – tiny steps for big tasks")  # CSS: assets/style.css

app.layout = dmc.MantineProvider(
    id="provider",
    forceColorScheme="light",
    theme={
        "primaryColor": "pink",
        "defaultRadius": "xl",
        "fontFamily": "Inter, 'Segoe UI', system-ui, sans-serif",
    },
    children=[
        dcc.Store(id="scheme", storage_type="local", data="light"),
        dmc.Container(
            [
                dmc.Group(
                    dmc.ActionIcon(
                        "🌙",
                        id="toggle",
                        variant="light",
                        color="pink",
                        size="xl",
                        radius="xl",
                        style={"fontSize": "1.4rem"},
                    ),
                    justify="flex-end",
                    pt="md",
                ),
                dmc.Stack(
                    [
                        dmc.Text("🦥", ta="center", style={"fontSize": "4.5rem", "lineHeight": 1}),
                        dmc.Text(
                            "Slothstep",
                            ta="center",
                            variant="gradient",
                            gradient=GRADIENT,
                            fw=900,
                            style={"fontSize": "4rem", "lineHeight": 1.1},
                        ),
                        dmc.Text(
                            "Describe what you keep putting off and get three tiny steps. "
                            "Powered by an open-weight model – no closed API.",
                            ta="center",
                            c="dimmed",
                            size="xl",
                        ),
                        dmc.Center(dmc.Badge(id="status", size="xl", radius="xl", variant="light")),
                        dcc.Interval(id="status-tick", interval=15_000),
                    ],
                    gap="sm",
                    pb="lg",
                ),
                dmc.Paper(
                    [
                        dmc.Stack(
                            [
                                dmc.Textarea(
                                    id="task",
                                    placeholder="What are you putting off?",
                                    autosize=True,
                                    minRows=3,
                                    size="xl",
                                    radius="xl",
                                ),
                                dmc.Center(
                                    dmc.Button(
                                        "Break it down for me",
                                        id="go",
                                        size="xl",
                                        radius=999,
                                        variant="gradient",
                                        gradient={"from": "pink", "to": "black", "deg": 90},
                                    )
                                ),
                            ],
                            gap="md",
                            p="xl",
                        ),
                        dmc.Stack(
                            [
                                dmc.Text("Try one:", size="md", c="gray.4"),
                                dmc.Group(
                                    [
                                        dmc.Button(
                                            text,
                                            id={"type": "example", "index": i},
                                            variant="filled",
                                            color="pink",
                                            size="md",
                                            radius="xl",
                                            styles={
                                                "root": {"border": "none"},
                                                "label": {"whiteSpace": "normal"},
                                            },
                                        )
                                        for i, text in enumerate(EXAMPLES)
                                    ],
                                    gap="xs",
                                ),
                            ],
                            gap="md",
                            p="xl",
                            style={"background": "#000"},
                        ),
                    ],
                    withBorder=True,
                    shadow="lg",
                    radius=32,
                    mb="xl",
                ),
                dcc.Loading(html.Div(id="result"), type="dot", color="#ec4899"),
                html.Div(style={"height": "4rem"}),
            ],
            size=860,
        ),
    ],
)


@app.callback(
    Output("provider", "forceColorScheme"),
    Output("scheme", "data"),
    Output("toggle", "children"),
    Input("toggle", "n_clicks"),
    State("scheme", "data"),
)
def toggle_scheme(n_clicks, scheme):
    scheme = scheme if scheme in {"light", "dark"} else "light"
    if n_clicks:
        scheme = "dark" if scheme == "light" else "light"
    return scheme, scheme, "☀️" if scheme == "dark" else "🌙"


@app.callback(
    Output("status", "children"),
    Output("status", "color"),
    Input("status-tick", "n_intervals"),
)
def update_status(_n):
    color, label = model_status()
    return label, {"success": "teal", "warning": "yellow", "danger": "red"}[color]


@app.callback(
    Output("task", "value"),
    Input({"type": "example", "index": dash.ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def fill_example(_clicks):
    trigger = dash.ctx.triggered_id
    if not trigger or not dash.ctx.triggered[0]["value"]:
        return dash.no_update
    return EXAMPLES[trigger["index"]]


@app.callback(
    Output("result", "children"),
    Input("go", "n_clicks"),
    State("task", "value"),
    prevent_initial_call=True,
)
def plan(_n, task):
    task = (task or "").strip()
    if not task:
        return dmc.Alert(
            "Describe a task and I will turn it into a plan.", color="yellow", radius=0
        )
    try:
        steps = make_plan(task)
    except RuntimeError as exc:
        return dmc.Alert(str(exc), color="red", title="Something went wrong", radius=0)
    total = sum(s["minutes"] for s in steps)
    return dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Text("Just start with the first tiny step", size="xl", fw=700),
                    dmc.Badge(
                        f"total ~{total} min", size="xl", radius=0, variant="outline", color="blue"
                    ),
                ],
                justify="space-between",
            ),
            *[step_card(i, s) for i, s in enumerate(steps, start=1)],
        ],
        gap="md",
    )


@app.callback(
    Output({"type": "txt", "index": dash.MATCH}, "td"),
    Output({"type": "txt", "index": dash.MATCH}, "c"),
    Input({"type": "done", "index": dash.MATCH}, "checked"),
)
def strike_done(done):
    return ("line-through", "dimmed") if done else (None, None)


server = app.server


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", 8050)))
