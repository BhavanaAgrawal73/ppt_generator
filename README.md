# PPT Generator — Text → PowerPoint (Template-Aware)

Turn bulk text or Markdown into a fully styled PowerPoint that matches an uploaded `.pptx/.potx` template.  
Keys are never stored. MIT Licensed.

## Features
- Paste long text/Markdown → intelligent slide split (5–20 slides)
- Tone/use-case guidance (investor, exec, research, etc.)
- Uses your uploaded PowerPoint template’s styles (colors, fonts, layouts, images)
- Auto speaker notes via LLM
- Preview + edit before download
- Any LLM provider with your own key (OpenAI/Anthropic/Gemini or AI Pipe gateway)
- Robust errors, size limits, retry logic

## Quick Start (local)
```bash
# 1) install
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt

# 2) (optional) AI Pipe / gateway base for OpenAI-compatible calls
export OPENAI_BASE="https://aipipe.org/openai/v1"   # or https://aipipe.org/openrouter/v1

# 3) run
uvicorn backend.main:app --host 0.0.0.0 --port 8000
# open http://127.0.0.1:8000/frontend/index.html
Using AI Pipe (model names)
Select Provider = OpenAI

Use namespaced models like:

openai/gpt-4o-mini (recommended)

openai/gpt-4o, openai/gpt-4.1-mini, openai/gpt-3.5-turbo

Put your AIPIPE_TOKEN in the app’s API Key box.

Other providers
Anthropic: anthropic/claude-3-5-sonnet-latest, etc.

Gemini: google/gemini-1.5-pro, google/gemini-1.5-flash

Frontend
frontend/index.html, app.js, styles.css

Served at /frontend by FastAPI

API (brief)
POST /analyze → returns slide outline JSON

POST /generate → uploads template + outline → returns .pptx

Deploy tips
Commit requirements.txt

Set OPENAI_BASE env if using a gateway

Max template size defaults to 20 MB
