"""
llm_service.py — Structured metadata extraction via Ollama.

Sends raw scraped hackathon text to a local Ollama model and returns
a clean JSON object with event_name, application_deadline, event_date,
college_name, and location.

Setup:
    1. Install Ollama: https://ollama.com/download
    2. Pull a model: `ollama pull mistral`
    3. Set OLLAMA_URL and LLM_MODEL in your .env (optional overrides)
"""

import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("llm_service")

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral")

EXTRACT_SYSTEM_PROMPT = (
    "You are a data parser. Your only job is to extract structured fields "
    "from raw hackathon event text. Output ONLY valid JSON — no explanation, "
    "no markdown fences, no extra text."
)

EXTRACT_USER_TEMPLATE = """Extract the following fields from the raw hackathon text below.

Fields to extract:
- event_name      : Full name of the event
- application_deadline : Registration / application deadline (date string or null)
- event_date      : Date(s) the event takes place (string or null)
- college_name    : Organising institution / college name (or null)
- location        : City or venue (or null)

Rules:
- Ignore UI noise such as match percentages (e.g. "34%"), buttons, or navigation labels.
- If a field cannot be determined, set it to null.
- Output ONLY a single JSON object. Example:
{{
  "event_name": "...",
  "application_deadline": "...",
  "event_date": "...",
  "college_name": "...",
  "location": "..."
}}

Raw text:
\"\"\"
{raw_text}
\"\"\"
"""


def extract_hackathon_metadata(raw_text: str) -> dict | None:
    """
    Sends raw scraped hackathon text to the local Ollama model.
    Returns a dict with extracted fields, or None if the call fails.

    Expected keys in the returned dict:
        event_name, application_deadline, event_date, college_name, location
    """
    prompt = EXTRACT_USER_TEMPLATE.format(raw_text=raw_text.strip())

    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "system": EXTRACT_SYSTEM_PROMPT,
        "stream": False,
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()

        raw_output = response.json().get("response", "").strip()

        # Parse the JSON the model returned
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            log.warning("LLM returned non-JSON output: %s", raw_output[:200])
            return None

    except requests.exceptions.ConnectionError:
        log.warning("Ollama not running at %s — cannot extract metadata.", OLLAMA_BASE_URL)
        return None

    except requests.exceptions.Timeout:
        log.warning("Ollama timed out while extracting metadata.")
        return None

    except Exception as e:
        log.error("extract_hackathon_metadata failed: %s", e)
        return None


def is_ollama_available() -> bool:
    """Quick health check — returns True if Ollama is reachable."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# ── Prompt templates for structure_scraped_hackathon ────────────

_STRUCTURE_SYSTEM = (
    "You are a specialized data parser for hackathon events. "
    "Your only output is valid JSON — no markdown, no explanation, no extra text."
)

_STRUCTURE_TEMPLATE = """You will be given raw text scraped from a hackathon listing page.
Extract and return a JSON object with EXACTLY these keys:

{{
  "event_name":           "<full event name>",
  "application_deadline": "<YYYY-MM-DD or null>",
  "event_start_date":     "<YYYY-MM-DD or null>",
  "college_name":         "<organising institution or null>",
  "location":             "<city or venue or null>",
  "short_summary":        "<2-3 sentence plain-English summary of the event>"
}}

Rules:
- Remove all UI noise: percentages like '34%', button labels, navigation text.
- Standardize all dates to YYYY-MM-DD format where possible. Set to null if unclear.
- short_summary must be clean, human-readable, max 3 sentences.
- If a field cannot be determined, set it to null.
- Output ONLY the JSON object, nothing else.

Raw scraped text:
\"\"\"
{raw_text}
\"\"\"
"""


def structure_scraped_hackathon(raw_text: str) -> dict | None:
    """
    Sends raw Playwright-scraped hackathon text to the local Ollama model
    and returns a clean structured dict.

    Returned keys:
        event_name, application_deadline, event_start_date,
        college_name, location, short_summary

    Returns None if Ollama is unreachable, times out, or returns invalid JSON.
    """
    prompt = _STRUCTURE_TEMPLATE.format(raw_text=raw_text.strip())

    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "system": _STRUCTURE_SYSTEM,
        "stream": False,
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=90,          # longer timeout — summary generation takes time
        )
        response.raise_for_status()

        raw_output = response.json().get("response", "").strip()

        # Strip markdown fences if the model wraps in ```json ... ```
        if raw_output.startswith("```"):
            raw_output = raw_output.split("```")[-2].strip()
            if raw_output.startswith("json"):
                raw_output = raw_output[4:].strip()

        try:
            return json.loads(raw_output)
        except json.JSONDecodeError as je:
            log.warning(
                "structure_scraped_hackathon: LLM returned invalid JSON (%s). "
                "Raw output (first 300 chars): %s",
                je, raw_output[:300],
            )
            return None

    except requests.exceptions.ConnectionError:
        log.warning("Ollama not running at %s — cannot structure hackathon.", OLLAMA_BASE_URL)
        return None

    except requests.exceptions.Timeout:
        log.warning("Ollama timed out while structuring hackathon text.")
        return None

    except Exception as e:
        log.error("structure_scraped_hackathon failed: %s", e)
        return None
