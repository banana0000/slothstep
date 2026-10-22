"""Slothstep: turn an overwhelming to-do into three quick steps, with an open-weight model."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html

MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
# Optional: any OpenAI-compatible host serving an open-weight model (used instead of Ollama).
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "").rstrip("/")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
EXAMPLES = [
    "I have to clean the whole flat because guests arrive on Saturday",
    "I need to write a long, difficult email to my boss",
    "I haven't sorted the files on my laptop in years",
]


def make_plan(task: str, model: str = MODEL, ollama_url: str = OLLAMA_URL) -> list[dict]:
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


def step_card(index: int, step: dict) -> dbc.Card:
    first = index == 1
    return dbc.Card(
        dbc.CardBody(
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(str(index), className="step-number"),
                        width="auto",
                    ),
                    dbc.Col(
                        [
                            dbc.Checkbox(
                                id={"type": "done", "index": index},
                                label=step["action"],
                                className="step-label",
                            ),
                            html.Small(
                                "Start here – this is all you need to do right now."
                                if first
                                else "Once the previous one is done.",
                                className="text-muted",
                            ),
                        ]
                    ),
                    dbc.Col(
                        dbc.Badge(
                            f"~{step['minutes']} min",
                            pill=True,
                            color="success" if first else "secondary",
                            className="fs-6",
                        ),
                        width="auto",
                    ),
                ],
                align="center",
                className="g-3",
            )
        ),
        className="mb-3 step-card shadow-sm" + (" step-first" if first else ""),
    )


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.LUX, dbc.icons.BOOTSTRAP],
    title="Slothstep – tiny steps for big tasks",
)

app.index_string = app.index_string.replace(
    "</head>",
    """<style>
    body { background: linear-gradient(160deg, #eef5ee 0%, #f8f4ec 100%); min-height: 100vh; }
    .hero h1 { font-weight: 700; }
    .step-card { border: 0; border-radius: 1rem; transition: transform .15s; }
    .step-card:hover { transform: translateY(-2px); }
    .step-first { border-left: 6px solid #3a9d5d; }
    .step-number { width: 2.6rem; height: 2.6rem; border-radius: 50%; background: #3a9d5d;
        color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; }
    .step-label { font-size: 1.1rem; }
    .main-card { border: 0; border-radius: 1.25rem; }
    .example-btn { white-space: normal; text-align: left; }
    </style></head>""",
)

app.layout = dbc.Container(
    [
        html.Div(
            [
                html.Div("🦥", style={"fontSize": "4rem"}),
                html.H1("Slothstep"),
                html.P(
                    "Describe what you keep putting off and get three tiny steps. "
                    "Powered by an open-weight model – no closed API.",
                    className="lead text-muted",
                ),
            ],
            className="hero text-center pt-5 pb-3",
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    dbc.Textarea(
                        id="task",
                        placeholder="What are you putting off?",
                        size="lg",
                        rows=3,
                        className="mb-3",
                    ),
                    dbc.Button(
                        [html.I(className="bi bi-magic me-2"), "Break it down for me"],
                        id="go",
                        color="success",
                        size="lg",
                        className="w-100",
                    ),
                    html.Div(
                        [
                            html.Small("Try one:", className="text-muted d-block mt-3 mb-1"),
                            *[
                                dbc.Button(
                                    text,
                                    id={"type": "example", "index": i},
                                    color="light",
                                    size="sm",
                                    className="example-btn me-2 mb-2",
                                )
                                for i, text in enumerate(EXAMPLES)
                            ],
                        ]
                    ),
                ]
            ),
            className="main-card shadow mb-4",
        ),
        dcc.Loading(html.Div(id="result"), type="dot", color="#3a9d5d"),
        html.Footer(
            f"Model: {MODEL} · open weights",
            className="text-center text-muted small py-4",
        ),
    ],
    style={"maxWidth": "720px"},
)


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
        return dbc.Alert("Describe a task and I will turn it into a plan.", color="warning")
    try:
        steps = make_plan(task)
    except RuntimeError as exc:
        return dbc.Alert(str(exc), color="danger")
    total = sum(s["minutes"] for s in steps)
    return [
        html.Div(
            [
                html.H4("Just start with the first tiny step", className="mb-0"),
                dbc.Badge(f"total ~{total} min", color="dark", pill=True),
            ],
            className="d-flex justify-content-between align-items-center mb-3",
        ),
        *[step_card(i, s) for i, s in enumerate(steps, start=1)],
    ]


@app.callback(
    Output({"type": "done", "index": dash.MATCH}, "className"),
    Input({"type": "done", "index": dash.MATCH}, "value"),
)
def strike_done(done):
    return "step-label text-decoration-line-through text-muted" if done else "step-label"


server = app.server


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", 8050)))
