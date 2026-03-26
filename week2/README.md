# Action Item Extractor

A FastAPI web application that extracts action items from freeform notes using either rule-based heuristics or a local LLM (via Ollama). Notes and extracted items are persisted in SQLite and displayed through a minimal vanilla JS frontend.

---

## Project Structure

```
week2/
├── app/
│   ├── main.py              # FastAPI app, lifespan, router mounts, static files
│   ├── db.py                # SQLite database layer
│   ├── schemas.py           # Pydantic request/response models
│   ├── routers/
│   │   ├── notes.py         # GET /notes, POST /notes, GET /notes/{id}
│   │   └── action_items.py  # Extraction and action item endpoints
│   └── services/
│       └── extract.py       # Heuristic and LLM extraction logic
├── frontend/
│   └── index.html           # Single-page frontend (HTML/CSS/JS)
├── tests/
│   └── test_extract.py      # Unit tests for extraction functions
└── data/
    └── app.db               # SQLite database (auto-created on first run)
```

---

## Setup

**Requirements:** Python 3.12, [Poetry](https://python-poetry.org/), [Ollama](https://ollama.com)

```bash
# From the repo root
conda create -n cs146s python=3.12
conda activate cs146s
poetry install --no-interaction
```

Pull the LLM model used for extraction:

```bash
ollama pull mistral:7b
```

---

## Running the App

```bash
PYTHONPATH=. uvicorn week2.app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## API Endpoints

### Notes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/notes` | List all saved notes |
| `POST` | `/notes` | Create a new note |
| `GET` | `/notes/{note_id}` | Retrieve a single note by ID |

**`POST /notes`** — request body:
```json
{ "content": "Your note text here" }
```

**Response:**
```json
{ "id": 1, "content": "Your note text here", "created_at": "2026-03-26 10:00:00" }
```

---

### Action Items

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/action-items/extract` | Extract action items using heuristics |
| `POST` | `/action-items/extract-llm` | Extract action items using LLM (Ollama/mistral:7b) |
| `GET` | `/action-items` | List all action items (optionally filter by `?note_id=`) |
| `POST` | `/action-items/{id}/done` | Mark an action item as done or not done |

**`POST /action-items/extract` and `/action-items/extract-llm`** — request body:
```json
{ "text": "- Fix the login bug\n- Write unit tests", "save_note": true }
```

**Response:**
```json
{
  "note_id": 1,
  "items": [
    { "id": 1, "text": "Fix the login bug" },
    { "id": 2, "text": "Write unit tests" }
  ]
}
```

**`POST /action-items/{id}/done`** — request body:
```json
{ "done": true }
```

---

## Extraction Methods

### Heuristic (`/extract`)
Rule-based extraction that detects:
- Bullet points (`-`, `*`, `•`, `1.`)
- Keyword prefixes (`todo:`, `action:`, `next:`)
- Checkbox markers (`[ ]`, `[todo]`)
- Imperative sentences as a fallback (e.g. lines starting with *fix*, *implement*, *write*)

### LLM (`/extract-llm`)
Uses [Ollama](https://ollama.com) with `mistral:7b` and structured JSON output (via Pydantic schema) to extract all tasks, follow-ups, and suggestions — including vague or tentative ones. Runs fully locally with no external API calls.

---

## Running Tests

```bash
PYTHONPATH=. pytest -q week2/tests/
```

Run a single test file or test:

```bash
PYTHONPATH=. pytest -q week2/tests/test_extract.py
PYTHONPATH=. pytest -q week2/tests/test_extract.py::test_llm_empty_input
```

Tests mock `ollama.chat` so no running Ollama instance is required.
