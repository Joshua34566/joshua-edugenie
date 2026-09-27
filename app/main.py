from __future__ import annotations

import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
load_dotenv(ROOT.parent / ".env")

API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
API_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
AI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

app = FastAPI(title="EduGenie", description="A friendly AI-powered learning assistant")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    level: str = "High school"


class QuizRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=300)
    level: str = "High school"


class PathRequest(BaseModel):
    subject: str = Field(min_length=2, max_length=300)
    level: str = "Beginner"
    hours_per_week: int = Field(default=4, ge=1, le=40)


class SummaryRequest(BaseModel):
    text: str = Field(min_length=30, max_length=16000)


class RecommendRequest(BaseModel):
    subject: str = Field(min_length=2, max_length=300)
    level: str = "Beginner"
    goal: str = Field(default="Build a strong foundation", max_length=500)


async def ask_model(system: str, user: str, *, json_mode: bool = False) -> str | None:
    """Use any OpenAI-compatible chat completion endpoint when configured."""
    if not API_KEY:
        return None
    payload: dict[str, Any] = {
        "model": AI_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0.5,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                f"{API_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json=payload,
            )
            if json_mode and response.status_code in (400, 422):
                # Some OpenAI-compatible servers do not implement response_format.
                payload.pop("response_format", None)
                response = await client.post(
                    f"{API_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    json=payload,
                )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        return None


def json_object(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            start, end = raw.find("{"), raw.rfind("}")
            if start < 0 or end < start:
                return None
            value = json.loads(raw[start : end + 1])
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None


def local_answer(question: str) -> str:
    q = question.lower()
    if "largest ocean" in q or "biggest ocean" in q:
        return "The Pacific Ocean is the largest ocean on Earth. It covers about 30% of the planet’s surface and is larger than all of Earth’s land area combined."
    if "pythag" in q or "right triangle" in q:
        return "The Pythagorean theorem says that for a right triangle, the squares of the two shorter sides add up to the square of the hypotenuse: a² + b² = c². For example, sides 3 and 4 give a hypotenuse of 5 because 3² + 4² = 5²."
    if re.search(r"\bsql\b", q):
        return "SQL is a language for working with data in relational databases. You can use SELECT to choose columns, FROM to choose a table, and WHERE to filter rows. For example: SELECT name FROM students WHERE grade >= 80;"
    if "photosynthesis" in q:
        return "Photosynthesis is how plants use sunlight to make sugar from water and carbon dioxide. It mainly happens in leaves, inside structures called chloroplasts, and releases oxygen as a by-product."
    if "river" in q and "ocean" in q:
        return "A river is flowing freshwater that usually moves across land toward a lake, another river, or the sea. An ocean is a vast, connected body of salty water. Rivers carry water and nutrients across land; oceans shape climate and support enormous ecosystems."
    if "gravity" in q:
        return "Gravity is the attraction between objects that have mass. Earth’s gravity pulls objects toward its center and keeps the Moon in orbit. More massive objects exert a stronger gravitational pull."
    return ("I’m in local mode, so my built-in reference is limited. Try a question about oceans and rivers, the Pythagorean theorem, SQL, photosynthesis, or gravity. "
            "You can connect an AI model in the environment settings to explore other topics.")


def local_quiz(topic: str) -> list[dict[str, Any]]:
    t = topic.lower()
    if "pythag" in t or "right triangle" in t:
        return [
            {"question": "Which equation expresses the Pythagorean theorem?", "choices": ["a + b = c", "a² + b² = c²", "a² − b² = c²", "2a + 2b = c"], "answer": 1, "explanation": "For a right triangle, the squares of the two legs add to the square of the hypotenuse."},
            {"question": "A right triangle has legs of 6 cm and 8 cm. How long is its hypotenuse?", "choices": ["9 cm", "10 cm", "12 cm", "14 cm"], "answer": 1, "explanation": "6² + 8² = 36 + 64 = 100, and √100 = 10."},
            {"question": "Which side is called the hypotenuse?", "choices": ["The shortest side", "Either side touching the right angle", "The side opposite the right angle", "Any side of equal length"], "answer": 2, "explanation": "The hypotenuse is always opposite the 90° angle and is the longest side."},
            {"question": "A triangle has side lengths 5, 12, and 13. Is it a right triangle?", "choices": ["Yes, because 5² + 12² = 13²", "No, because 5 + 12 ≠ 13", "Yes, because all sides are different", "There is not enough information"], "answer": 0, "explanation": "25 + 144 = 169, so the Pythagorean relationship holds."},
        ]
    if re.search(r"\bsql\b", t):
        return [
            {"question": "Which SQL command retrieves rows from a table?", "choices": ["SELECT", "UPDATE", "CREATE", "DROP"], "answer": 0, "explanation": "SELECT reads data from one or more tables."},
            {"question": "What does a WHERE clause do?", "choices": ["Renames a table", "Filters rows by a condition", "Sorts columns alphabetically", "Deletes a database"], "answer": 1, "explanation": "WHERE keeps only rows that match its condition."},
            {"question": "Which clause sorts query results?", "choices": ["GROUP BY", "ORDER BY", "FILTER BY", "SORT"], "answer": 1, "explanation": "ORDER BY sorts rows by one or more columns."},
            {"question": "What does COUNT(*) return?", "choices": ["The number of rows", "The longest text value", "The first row", "The number of tables"], "answer": 0, "explanation": "COUNT(*) counts all rows in the selected result set."},
        ]
    if "ocean" in t or "river" in t:
        return [
            {"question": "Which is the largest ocean on Earth?", "choices": ["Atlantic", "Indian", "Pacific", "Arctic"], "answer": 2, "explanation": "The Pacific is the largest and deepest ocean."},
            {"question": "What kind of water do most rivers carry?", "choices": ["Freshwater", "Saltwater", "Distilled water", "Only rainwater"], "answer": 0, "explanation": "Most rivers carry freshwater from higher land toward lakes or seas."},
            {"question": "Which statement best describes an ocean?", "choices": ["A small freshwater stream", "A vast body of salty water", "A lake surrounded by land", "Water stored underground"], "answer": 1, "explanation": "Oceans are the planet’s vast connected bodies of salt water."},
            {"question": "Where does a river commonly flow?", "choices": ["Uphill toward its source", "Across land toward a lake, river, or sea", "Only beneath the ground", "In a permanent circle"], "answer": 1, "explanation": "Rivers generally flow downhill toward another body of water."},
        ]
    # Open-ended prompts stay honest in local mode: there is no invented answer key.
    return [
        {"question": f"In your own words, what is the main idea of {topic}?", "choices": [], "answer": None, "explanation": "A strong answer names the central idea and explains it clearly."},
        {"question": f"What is one important term or building block in {topic}?", "choices": [], "answer": None, "explanation": "Define the term and explain how it connects to the broader topic."},
        {"question": f"How could you use an idea from {topic} in a real example?", "choices": [], "answer": None, "explanation": "Use a specific situation and connect it to a relevant concept."},
        {"question": f"What part of {topic} would you like to learn more about, and why?", "choices": [], "answer": None, "explanation": "This reflection helps identify your next learning step."},
    ]


def local_path(subject: str, level: str, hours: int) -> dict[str, Any]:
    if re.search(r"\bsql\b|database", subject.lower()):
        stages = [
            {"title": "Get comfortable with tables", "duration": "Week 1", "topics": ["Rows, columns, and data types", "Tables and primary keys", "Reading a simple schema"], "project": "Sketch a small library database with books and borrowers."},
            {"title": "Ask useful questions", "duration": "Weeks 2–3", "topics": ["SELECT and aliases", "WHERE and comparison operators", "ORDER BY and LIMIT"], "project": "Write queries to find and sort books by author or year."},
            {"title": "Connect related data", "duration": "Weeks 4–5", "topics": ["COUNT, SUM, and AVG", "GROUP BY and HAVING", "INNER and LEFT JOIN"], "project": "Report how many books each borrower has checked out."},
            {"title": "Build reliable queries", "duration": "Weeks 6–7", "topics": ["Subqueries and common table expressions", "INSERT, UPDATE, and DELETE", "Indexes and query plans"], "project": "Create a small reading tracker and explain how you would keep queries fast."},
        ]
        timeframe = f"About 7 weeks at {hours} hours per week"
    else:
        stages = [
            {"title": "Build the foundation", "duration": "Week 1", "topics": [f"Core vocabulary in {subject}", "How the main ideas fit together", "A short beginner overview"], "project": "Create a one-page concept map of the key ideas."},
            {"title": "Learn the core skills", "duration": "Weeks 2–3", "topics": ["Work through one idea at a time", "Follow a worked example", "Practice with short exercises"], "project": "Explain one core idea with your own example."},
            {"title": "Practice and connect", "duration": "Weeks 4–5", "topics": ["Apply ideas to new problems", "Compare related concepts", "Review mistakes and gaps"], "project": "Complete a small project or set of mixed practice questions."},
            {"title": "Go deeper", "duration": "Weeks 6–7", "topics": ["Explore an advanced topic", "Read a trusted source", "Teach back what you learned"], "project": "Make a short guide that helps another learner get started."},
        ]
        timeframe = f"A flexible 7-week starter plan at {hours} hours per week"
    return {"title": f"Your {subject} learning path", "timeframe": timeframe, "stages": stages,
            "note": f"This path starts at {level.lower()} level. Adjust the pace around your schedule and revisit earlier topics whenever you need to."}


def local_recommendations(subject: str, level: str, goal: str) -> list[dict[str, str]]:
    if "sql" in subject.lower():
        recs = [
            ("Try a tiny dataset", f"At {level.lower()} level, a few rows you can inspect by eye make filters and joins easier to understand.", "Create a table of 5 books and find the newest one."),
            ("Practice one query pattern", "Small, repeated exercises build fluency faster than memorizing syntax.", "Write three SELECT queries with different WHERE conditions."),
            ("Explain your result", "Saying why each row appears is a good check that the query matches your intention.", "Predict the result before running a query, then compare."),
        ]
    else:
        recs = [
            ("Start with one clear question", f"For a {level.lower()} learner studying {subject}, a focused question makes a study session easier to finish.", f"Write down one question related to: {goal}."),
            ("Learn, then retrieve", "After reading a short section, close it and recall the main points from memory.", "Spend 10 minutes learning, then write a 3-line explanation."),
            ("Use a worked example", "A concrete example shows how an idea works before you practice it on your own.", f"Find one beginner example of {subject} and annotate each step."),
        ]
    return [{"title": title, "why": why, "action": action, "time": "10–20 min"} for title, why, action in recs]


def local_summary(text: str) -> tuple[str, list[str]]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if len(s.strip()) > 20]
    if not sentences:
        summary = " ".join(text.split()[:45])
        return summary, [summary] if summary else []
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    stop_words = {"the", "and", "that", "this", "with", "from", "were", "have", "their", "they", "which", "when", "into", "also", "than", "then", "what", "where", "because", "about", "while", "each", "such", "these", "those", "been", "being", "will", "would", "could", "should", "over", "under", "after", "before", "there", "here", "more", "most", "some", "many", "very", "just", "only", "like", "your", "them", "its", "our", "you", "for", "are", "was", "but", "not", "can", "all", "one", "out", "how", "has", "had", "who", "his", "her", "she", "him", "may", "use", "used"}
    common = Counter(w for w in words if w not in stop_words)
    ranked = sorted(
        enumerate(sentences),
        key=lambda item: (
            sum(common[w] for w in re.findall(r"[a-zA-Z]{3,}", item[1].lower())) / max(len(item[1].split()), 1),
            -item[0],
        ),
        reverse=True,
    )
    selected = sorted((index, sentence) for index, sentence in ranked[: min(3, len(sentences))])
    key_points = [sentence for _, sentence in selected]
    # Extractive fallback is deliberately identified as such in the response.
    summary = " ".join(sentence for _, sentence in selected)
    return summary, key_points


@app.get("/")
async def home() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
async def health() -> dict[str, str | bool]:
    return {"ok": True, "mode": "cloud" if API_KEY else "local", "model": AI_MODEL if API_KEY else "built-in reference"}


@app.post("/api/ask")
async def ask(request: AskRequest) -> dict[str, str]:
    answer = await ask_model(
        "You are EduGenie, a patient tutor. Give a concise, accurate answer at the learner's level. Use plain language and one helpful example where useful. If unsure, say so.",
        f"Learner level: {request.level}\nQuestion: {request.question}",
    )
    return {"answer": answer or local_answer(request.question), "mode": "cloud" if answer else "local"}


@app.post("/api/quiz")
async def quiz(request: QuizRequest) -> dict[str, Any]:
    prompt = (
        f"Create a 4-question quiz about {request.topic!r} for a {request.level} learner. "
        "Return JSON with key questions, an array of objects. Each object needs question, choices (4 short strings), "
        "answer (zero-based integer index), and explanation (one sentence). Questions should test understanding, not trivia."
    )
    generated = json_object(await ask_model("You write clear educational quizzes. Return valid JSON only.", prompt, json_mode=True))
    questions = generated.get("questions") if generated else None
    valid = isinstance(questions, list) and len(questions) > 0 and all(
        isinstance(item, dict) and isinstance(item.get("question"), str) and
        (item.get("choices") == [] or (isinstance(item.get("choices"), list) and len(item["choices"]) == 4)) and
        (item.get("answer") is None or (isinstance(item.get("answer"), int) and 0 <= item["answer"] < len(item.get("choices", []))))
        for item in questions
    )
    if not valid:
        questions = local_quiz(request.topic)
        mode = "local"
    else:
        mode = "cloud"
    return {"topic": request.topic, "questions": questions, "mode": mode}


@app.post("/api/learning-path")
async def learning_path(request: PathRequest) -> dict[str, Any]:
    prompt = (
        f"Design a practical learning path for {request.subject!r}. Starting level: {request.level}. "
        f"Available time: {request.hours_per_week} hours per week. Return JSON with title, timeframe, note, and stages. "
        "Provide 4 stages; each stage has title, duration, topics (3 strings), and project (one practical task)."
    )
    generated = json_object(await ask_model("You are an expert learning designer. Make plans achievable and specific. Return valid JSON only.", prompt, json_mode=True))
    stages = generated.get("stages") if generated else None
    if not isinstance(stages, list) or not stages or not all(isinstance(s, dict) and isinstance(s.get("title"), str) for s in stages):
        result = local_path(request.subject, request.level, request.hours_per_week)
        mode = "local"
    else:
        result = generated
        mode = "cloud"
    return {**result, "mode": mode}


@app.post("/api/summarize")
async def summarize(request: SummaryRequest) -> dict[str, Any]:
    prompt = (
        "Summarize the passage for a student. Return JSON with summary (2–4 concise sentences) and key_points (3–5 short strings).\n\n"
        + request.text
    )
    generated = json_object(await ask_model("You make accurate study notes. Preserve the passage's meaning and do not add unsupported facts. Return valid JSON only.", prompt, json_mode=True))
    if generated and isinstance(generated.get("summary"), str) and isinstance(generated.get("key_points"), list):
        return {"summary": generated["summary"], "key_points": generated["key_points"], "mode": "cloud"}
    summary, points = local_summary(request.text)
    return {"summary": summary, "key_points": points, "mode": "local"}


@app.post("/api/recommendations")
async def recommendations(request: RecommendRequest) -> dict[str, Any]:
    prompt = (
        f"Recommend 3 specific next learning actions for a {request.level} learner studying {request.subject!r}. "
        f"Their goal is: {request.goal}. Return JSON with items, an array of objects containing title, why, action, time."
    )
    generated = json_object(await ask_model("You are a supportive study coach. Give practical, varied suggestions. Return valid JSON only.", prompt, json_mode=True))
    items = generated.get("items") if generated else None
    if not isinstance(items, list) or not items or not all(isinstance(i, dict) and isinstance(i.get("title"), str) for i in items):
        items = local_recommendations(request.subject, request.level, request.goal)
        mode = "local"
    else:
        mode = "cloud"
    return {"subject": request.subject, "items": items, "mode": mode}

