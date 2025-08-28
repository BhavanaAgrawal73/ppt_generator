# PPT GENERATOR

## Text → PowerPoint (Template‑Aware)

Public web app to convert long text/Markdown into a **template‑faithful** PowerPoint. Users paste text, add an optional tone/guidance, select their LLM (OpenAI/Anthropic/Gemini) with **their own key**, upload a **.pptx/.potx** template, preview the outline, and download a ready‑styled **.pptx** that inherits **styles, layouts, colors, fonts, and reuses images** from the uploaded file. **No AI image generation**.

## Features
- Paste large text / Markdown
- One‑line guidance (tone/use case)
- Bring‑your‑own key: OpenAI, Anthropic, or Gemini (never stored or logged)
- Upload .pptx/.potx template or presentation
- LLM builds outline + **speaker notes for every slide**
- Edit outline in browser, preview slide cards
- Generate styled .pptx that inherits the template’s look & feel
- Tries to reuse images present in the template where picture placeholders exist
- Robust errors, 20 MB upload cap, retries for LLM calls
- MIT License, ready for public deployment

## Project Structure
text-to-pptx/

├─ backend/
│  ├─ main.py
│  ├─ llm_providers.py
│  ├─ pptx_builder.py
│  ├─ models.py
│  ├─ security.py
├─ frontend/
│  ├─ index.html
│  ├─ app.js
│  └─ styles.css
├─ .gitignore
├─ requirements.txt
├─ Dockerfile
├─ LICENSE
└─ README.md


## Quick Start (Local)
```bash
# 1) Clone
git clone https://github.com/YOUR-USER/text-to-pptx.git
cd text-to-pptx

# 2) (Optional) Create a venv
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# 3) Install deps
pip install -r requirements.txt

# 4) (optional) AI Pipe / gateway base for OpenAI-compatible calls
export OPENAI_BASE="https://aipipe.org/openai/v1"   # or https://aipipe.org/openrouter/v1

# 5) Run server
uvicorn backend.main:app --host 0.0.0.0 --port 8000
# Open http://127.0.0.1:8000/frontend/index.html  (or serve files from any static host)
```

If you open the root at `http://127.0.0.1:8000`, you’ll see only the API. To load the UI directly, open the `frontend/index.html` file in your browser or serve the `frontend/` folder via any static server (e.g. VS Code Live Server).
## Using AI Pipe (model names)
  * Select Provider = OpenAI
  * Use namespaced models like:
    * openai/gpt-4o-mini (recommended)
    * openai/gpt-4o, openai/gpt-4.1-mini, openai/gpt-3.5-turbo
  * Put your AIPIPE_TOKEN in the app’s API Key box.
## Other providers
   * Anthropic: anthropic/claude-3-5-sonnet-latest, etc.
   * Gemini: google/gemini-1.5-pro, google/gemini-1.5-flash

## Deploy (Render — recommended for non‑coders)

1. Create a new **Web Service** on [Render](https://render.com/), choose **Deploy an existing repo** and select this repo.
2. Render reads `Dockerfile` and `render.yaml` and will auto‑deploy.
3. Once live, visit `https://your-app.onrender.com/frontend/index.html`.

### Deploy (Railway)

1. Create a new project → **Deploy from GitHub Repo**.
2. Railway will detect the Dockerfile. Expose **Port 8000**.
3. After deploy, open the domain at `/frontend/index.html`.

## How It Works

1. **/analyze**: Sends your text + guidance to the chosen LLM with strict JSON instructions. Returns an editable `SlideDeck` (titles, bullets, notes).
2. **Preview**: The UI shows each slide as a card. You can edit titles, bullets, and notes.
3. **/generate**: Backend creates a new presentation using your uploaded template, adding slides with matching layouts. If picture placeholders exist and the template had images, the app reuses them.

> **Privacy**: API keys are only used to call the provider for your single request. They are not saved to disk, not echoed to logs, and never sent anywhere else. You can also self‑host to keep full control.

## Design Choices & Limitations

* **Preview** is HTML-based for speed. Final .pptx will reflect the template faithfully (fonts/colors/layouts) through PowerPoint’s theme inheritance.
* **Image reuse** is best‑effort: we search for images in the template/presentation and place them into picture placeholders when present.
* This project **does not** generate new images via AI.

## Common Use‑Case Guidance (clickable in UI)

* Investor pitch deck
* Sales deck with visuals
* Academic research summary
* Executive summary for leadership
* Technical architecture review

## Troubleshooting

* "LLM failed": Double‑check your **provider** choice, **model** (or leave blank), and **API key**. Some providers require specific model IDs.
* "Payload too large": Keep the template under **20 MB**.
* Slides look plain in preview: That’s expected; the final .pptx inherits the template style.

## Security Notes

* API keys are never persisted and request bodies aren’t logged. See `backend/security.py`.
* Consider restricting CORS to your own domain after you deploy.

## Contributing

MIT licensed. PRs welcome!

=======




