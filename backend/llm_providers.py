import json
import re
import os
from typing import Dict, Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

# =========================
# Prompts
# =========================
SYSTEM_PROMPT = (
    "You convert long text or Markdown into a concise, well-structured slide deck. "
    "You MUST answer as strict JSON with keys: slides:[{title, bullets[], layout_hint, notes}], tone, use_case. "
    "Pick a reasonable number of slides (5–20) depending on length and guidance. "
    "Each slide: short title, 3–6 bullets max. Always include speaker notes (1–3 short paragraphs)."
)

USER_PROMPT_TMPL = (
    "Input text (can be Markdown):\n\n{raw_text}\n\n"
    "Guidance/tone/use-case (optional): {guidance}\n\n"
    "Return STRICT JSON only, no prose."
)

# =========================
# Helpers
# =========================
def _extract_json_maybe(text: str) -> Dict[str, Any]:
    """Extract a JSON object from model output (handles ```json fences or prose-wrapped JSON)."""
    if not text:
        raise ValueError("Empty response from model")

    m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.S | re.I)
    if m:
        return json.loads(m.group(1))

    m = re.search(r"(\{.*\})", text, flags=re.S)
    if m:
        return json.loads(m.group(1))

    return json.loads(text)

def _raise_for_provider_error(resp: httpx.Response, provider_label: str):
    try:
        body = resp.text[:500]
    except Exception:
        body = "<no body>"
    raise httpx.HTTPStatusError(
        f"{provider_label} HTTP {resp.status_code}: {body}",
        request=resp.request, response=resp
    )

# =========================
# Entry point with retries
# =========================
@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=8))
async def generate_slide_outline(provider: str, model: str, api_key: str, raw_text: str, guidance: str) -> Dict[str, Any]:
    payload = {
        "system": SYSTEM_PROMPT,
        "user": USER_PROMPT_TMPL.format(raw_text=raw_text[:60000], guidance=guidance[:200])
    }

    provider = (provider or "").strip().lower()

    if provider == "openai":  # Use this for AI-Pipe (OpenAI-compatible)
        return await _call_openai(model or "gpt-4o-mini", api_key, payload)
    elif provider == "anthropic":
        return await _call_anthropic(model or "claude-3-5-sonnet-latest", api_key, payload)
    elif provider == "gemini":
        return await _call_gemini(model or "gemini-1.5-pro", api_key, payload)
    else:
        raise ValueError("Unsupported provider. Use openai|anthropic|gemini.")

# =========================
# OpenAI-compatible (AI-Pipe)
# =========================
async def _call_openai(model: str, api_key: str, p: Dict[str, str]) -> Dict[str, Any]:
    """
    Works with api.openai.com and OpenAI-compatible gateways like AI-Pipe.
    Set OPENAI_BASE to your gateway URL (see README/.env).
    """
    base = os.getenv("OPENAI_BASE", "https://api.openai.com/v1")
    # accept either full /chat/completions or just /v1
    url = base if base.endswith("/chat/completions") else base.rstrip("/") + "/chat/completions"

    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "model": model,
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": p["system"]},
            {"role": "user",   "content": p["user"]},
        ],
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, json=data)
        if r.status_code >= 400:
            _raise_for_provider_error(r, "OpenAI-compatible")
        j = r.json()
        content = j["choices"][0]["message"]["content"]
        return _extract_json_maybe(content)

# =========================
# Anthropic
# =========================
async def _call_anthropic(model: str, api_key: str, p: Dict[str, str]) -> Dict[str, Any]:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    data = {
        "model": model,
        "max_tokens": 4096,
        "temperature": 0.3,
        "system": p["system"],
        "messages": [{"role": "user", "content": p["user"]}],
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, json=data)
        if r.status_code >= 400:
            _raise_for_provider_error(r, "Anthropic")
        j = r.json()
        content = "".join([blk.get("text", "") for blk in j.get("content", [])])
        return _extract_json_maybe(content)

# =========================
# Gemini (native)
# =========================
async def _call_gemini(model: str, api_key: str, p: Dict[str, str]) -> Dict[str, Any]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    data = {
        "systemInstruction": {"parts": [{"text": p["system"]}]},
        "contents": [{"role": "user", "parts": [{"text": p["user"]}]}],
        "generationConfig": {
            "temperature": 0.3,
            "response_mime_type": "application/json",
            "maxOutputTokens": 4096,
        },
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=data)
        if r.status_code >= 400:
            _raise_for_provider_error(r, "Gemini")
        j = r.json()
        if not j.get("candidates"):
            raise ValueError(f"Gemini returned no candidates: {j}")
        cand = j["candidates"][0]
        parts = cand.get("content", {}).get("parts", [])
        if not parts:
            raise ValueError(f"Gemini returned empty parts: {j}")
        text = parts[0].get("text", "")
        return _extract_json_maybe(text)
