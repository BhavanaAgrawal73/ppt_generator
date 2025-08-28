import io
import json
import logging
import os
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

from .llm_providers import generate_slide_outline
from .pptx_builder import build_presentation, collect_template_images
from .models import AnalyzeResponse, GenerateRequest, SlideDeck
from .security import MAX_FILE_SIZE_BYTES, mask_api_key, safe_len

app = FastAPI(title="Text→PPTX (Template-Aware)", version="1.0.0")

# Serve the frontend folder at /frontend
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

# CORS — allow public use (you can restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- FIXED LOGGING ----------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("text2pptx")
logger.info("OPENAI_BASE = %s", os.getenv("OPENAI_BASE", "(default: api.openai.com)"))
# -----------------------------------

@app.get("/")
def root():
    return RedirectResponse(url="/frontend/index.html")

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: Request,
    text: str = Form(..., description="Bulk text or Markdown"),
    guidance: str = Form("", description="One-line guidance for tone/use case"),
    provider: str = Form(..., description="openai|anthropic|gemini"),
    model: str = Form("", description="Model id, optional"),
    api_key: str = Form(..., description="Provider API key (never stored)"),
    template: UploadFile = File(..., description=".pptx or .potx template/presentation")
):
    # Basic validations
    if not text or safe_len(text) < 10:
        raise HTTPException(422, detail="Please paste more text (≥10 chars).")

    if template.content_type not in ("application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                     "application/vnd.openxmlformats-officedocument.presentationml.template") and not template.filename.lower().endswith((".pptx", ".potx")):
        raise HTTPException(415, detail="Upload a .pptx or .potx file.")

    # Enforce upload size limit
    body_len = request.headers.get("content-length")
    try:
        if body_len and int(body_len) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(413, detail=f"Payload too large (> {MAX_FILE_SIZE_BYTES // (1024*1024)} MB).")
    except ValueError:
        pass

    template_bytes = await template.read()
    if len(template_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(413, detail=f"Template too large (> {MAX_FILE_SIZE_BYTES // (1024*1024)} MB).")

    # Extract a few reusable images (if any) for later re-use
    try:
        sample_image_blobs = collect_template_images(io.BytesIO(template_bytes), limit=8)
    except Exception as e:
        logger.warning(f"Could not collect images from template: {e}")
        sample_image_blobs = []

    # Ask the LLM to produce a structured outline
    try:
        slides_json = await generate_slide_outline(
            provider=provider.strip().lower(),
            model=model.strip(),
            api_key=api_key.strip(),
            raw_text=text,
            guidance=guidance,
        )
    except Exception as e:
        logger.error(f"LLM error: {str(e)} (key={mask_api_key(api_key)})")
        raise HTTPException(502, detail=f"LLM failed: {str(e)}")

    # Validate into our pydantic model
    try:
        deck = SlideDeck.model_validate(slides_json)
    except ValidationError as ve:
        raise HTTPException(500, detail=f"Bad LLM output. {ve}")

    # Build a minimal theme summary (best-effort; actual styling comes from template)
    theme_summary = {
        "templateFilename": template.filename,
        "reusableImageCount": len(sample_image_blobs),
        "note": "Preview is an approximation; final PPTX inherits exact styles from template."
    }

    return AnalyzeResponse(deck=deck, theme_summary=theme_summary)

@app.post("/generate")
async def generate(
    deck_json: str = Form(..., description="SlideDeck JSON from /analyze (possibly edited)"),
    template: UploadFile = File(..., description="Same .pptx/.potx uploaded again"),
    # Optional: re-generate/augment speaker notes with LLM if empty
    provider: str = Form(""),
    model: str = Form(""),
    api_key: str = Form("")
):
    try:
        deck = SlideDeck.model_validate_json(deck_json)
    except ValidationError as ve:
        raise HTTPException(422, detail=f"Invalid deck JSON: {ve}")

    template_bytes = await template.read()
    if len(template_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(413, detail=f"Template too large (> {MAX_FILE_SIZE_BYTES // (1024*1024)} MB).")

    # If any slide is missing notes and user provided an LLM key, fill them
    if api_key and provider:
        try:
            deck.fill_missing_notes = True
            deck.llm = {"provider": provider, "model": model, "api_key": mask_api_key(api_key)}
        except Exception:
            pass

    # Build PPTX
    try:
        pptx_bytes = build_presentation(io.BytesIO(template_bytes), deck)
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to build PPTX: {e}")

    filename = "generated_presentation.pptx"
    return StreamingResponse(
        io.BytesIO(pptx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
