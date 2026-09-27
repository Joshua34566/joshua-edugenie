# EduGenie

EduGenie is a lightweight study assistant with a FastAPI backend and a responsive HTML, CSS, and JavaScript interface. It supports concise answers, quick quizzes, structured learning paths, passage summaries, and personalized study suggestions.

## Run locally

Use Python 3.10 or newer.

```bash
python -m venv .venv
```

Activate the virtual environment (macOS/Linux: `source .venv/bin/activate`; Windows PowerShell: `.\.venv\Scripts\Activate.ps1`), then install and start the app:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Deploy online

The repository includes a `render.yaml` Blueprint for deploying the FastAPI app as a Render web service. Push this project to a GitHub repository, then create a new Blueprint in Render and connect that repository. Render will install `requirements.txt`, start Uvicorn on its assigned port, and check `/api/health`.

The service works without an API key using the built-in local guides. To enable cloud generation, add `OPENAI_API_KEY` and, if needed, `OPENAI_BASE_URL` and `OPENAI_MODEL` as environment variables in the hosting dashboard. Keep secrets out of the repository. The public app currently has no per-user authentication or AI usage limits, so add those before enabling a paid API key for unrestricted public use.

## Local and cloud modes

The app works without credentials. Local mode includes reference answers for the ocean and river, Pythagorean theorem, SQL, photosynthesis, and gravity examples; focused built-in quizzes for Pythagoras, SQL, oceans, and rivers; a SQL learning path; general learning-plan and study suggestions; and an extractive passage summary. Open-ended quiz topics return reflection questions without a made-up answer key.

To enable broader generation, copy `.env.example` to `.env`, add an API key, and set the model name supported by your provider. The backend calls the OpenAI-compatible `/chat/completions` API. `OPENAI_BASE_URL` can point to another compatible provider or a local model server. Restart the app after changing the environment.

The interface labels each result as AI assisted or a local guide. If a cloud request fails or returns an unusable response, the feature falls back to its local behavior.

## API

- `GET /api/health` — reports whether a cloud key is configured.
- `POST /api/ask` — answer a learner question.
- `POST /api/quiz` — generate a topic quiz.
- `POST /api/learning-path` — build a paced learning path.
- `POST /api/summarize` — summarize a passage and list key points.
- `POST /api/recommendations` — suggest next study actions.

Interactive API documentation is available at `/docs` while the server is running.

