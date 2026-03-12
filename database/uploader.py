import json
import os
import logging
from qdrant_client.http.models import Distance, VectorParams, PointStruct, TextIndexParams, TokenizerType

from database.qdrant_db import db, COLLECTION_NAME
from models.embedding_model import get_embedding
from scraper.parser import parse_event
from api.llm_service import enrich_event_for_qdrant

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("uploader")

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw_events.json')

# ── ANSI colours for pretty terminal output ──────────────────────
_G = "\033[92m"   # green
_Y = "\033[93m"   # yellow
_R = "\033[91m"   # red
_C = "\033[96m"   # cyan
_B = "\033[1m"    # bold
_X = "\033[0m"    # reset


def _fmt_payload(p: dict) -> str:
    """Render a payload dict as a pretty, coloured block for the terminal."""
    lines = [f"{_B}{_C}┌─ Structured Event ────────────────────────────────{_X}"]
    fields = [
        ("title",            "📌 Title"),
        ("date",             "📅 Date"),
        ("location",         "📍 Location"),
        ("fee",              "💰 Fee"),
        ("prize",            "🏆 Prize"),
        ("domains",          "🏷️ Domains"),
        ("problem_statements","🧩 Prob. Stmts"),
        ("registration_url", "🔗 Register"),
        ("visit_url",        "🌐 Visit"),
    ]
    for key, label in fields:
        val = p.get(key)
        
        # If value is a list (like domains or problem_statements), join it
        if isinstance(val, list):
            if val:
                display = ", ".join(val)
                # truncate if it's too long
                if len(display) > 50:
                    display = display[:47] + "..."
                colour = _G
            else:
                display = "—"
                colour = _Y
        else:
            colour = _G if val else _Y
            display = val if val else "—"
            
        lines.append(f"{_C}│{_X}  {label:<18} {colour}{display}{_X}")
    lines.append(f"{_B}{_C}└────────────────────────────────────────────────{_X}")
    return "\n".join(lines)


def seed_database(force_recreate=False):
    collections = db.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)

    if force_recreate or not exists:
        log.info("Setting up Qdrant collection: %s …", COLLECTION_NAME)
        db.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        
    else:
        log.info("Collection %s already exists. Skipping recreation.", COLLECTION_NAME)

    # Ensure Full-Text Search indexes exist (safe to call even if they exist)
    log.info("Ensuring payload indexes for hybrid search exist...")
    for field in ["title", "domains", "clean_description"]:
        try:
            db.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field,
                field_schema=TextIndexParams(
                    type="text",
                    tokenizer=TokenizerType.WORD,
                    min_token_len=2,
                    max_token_len=20,
                    lowercase=True,
                )
            )
        except Exception:
            # Index might already exist, which is fine
            pass

    log.info("Reading data from %s …", DATA_PATH)
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        events = json.load(f)

    log.info("Loaded %d raw events. Starting Ollama enrichment + embedding…\n", len(events))

    points = []
    for idx, raw_event in enumerate(events):
        title = raw_event.get("title", f"Event #{idx+1}")
        log.info("[%d/%d] Processing: %s", idx + 1, len(events), title[:50])

        # ── 1. Parse with regex first (always available) ──────────
        parsed = parse_event(raw_event)

        # ── 2. Try Ollama Mistral enrichment ──────────────────────
        enriched = enrich_event_for_qdrant(raw_event)

        if enriched:
            log.info("  %s[Ollama ✓]%s Mistral/Qwen returned structured data.", _G, _X)
            domains = enriched.get("domains") or parsed.get("domains") or []
            if "Knowafest" not in domains:
                domains.append("Knowafest")
            
            payload = {
                "title":            enriched.get("title")            or parsed.get("title"),
                "date":             enriched.get("date")             or parsed.get("date"),
                "location":         enriched.get("location")         or parsed.get("location"),
                "fee":              enriched.get("fee")              or parsed.get("fee"),
                "prize":            enriched.get("prize")            or parsed.get("prize"),
                "registration_url": enriched.get("registration_url") or parsed.get("registration_url"),
                "visit_url":        parsed.get("visit_url"),
                "clean_description": enriched.get("clean_description") or parsed.get("short_summary"),
                "domains":          domains,
                "problem_statements": enriched.get("problem_statements") or parsed.get("problem_statements") or [],
            }
        else:
            log.warning(
                "  %s[Ollama ✗]%s Falling back to regex-parsed values.", _Y, _X
            )
            domains = parsed.get("domains") or []
            if "Knowafest" not in domains:
                domains.append("Knowafest")

            payload = {
                "title":            parsed.get("title"),
                "date":             parsed.get("date"),
                "location":         parsed.get("location"),
                "fee":              parsed.get("fee"),
                "prize":            parsed.get("prize"),
                "registration_url": parsed.get("registration_url"),
                "visit_url":        parsed.get("visit_url"),
                "clean_description": parsed.get("short_summary"),
                "domains":          domains,
                "problem_statements": parsed.get("problem_statements") or [],
            }

        # ── 3. Pretty-print the structured event ──────────────────
        print(_fmt_payload(payload))
        print()

        # ── 4. Embed — use all available text for richer vectors ──
        domains_str = ", ".join(payload.get("domains", []))
        problems_str = " ".join(payload.get("problem_statements", []))
        embed_text = (
            f"Title: {payload['title']}. "
            f"Location: {payload['location']}. "
            f"Date: {payload['date']}. "
            f"Fee: {payload['fee']}. "
            f"Prize: {payload['prize']}. "
            f"Domains: {domains_str}. "
            f"Problem Statements: {problems_str}. "
            f"Description: {payload['clean_description']}."
        )
        vector = get_embedding(embed_text)

        points.append(PointStruct(id=idx + 1, vector=vector, payload=payload))

    log.info("Uploading %d structured vectors to Qdrant Cloud…", len(points))
    db.upsert(collection_name=COLLECTION_NAME, points=points)
    log.info("%s✅  Qdrant database fully loaded with %d events.%s", _G, len(points), _X)


if __name__ == "__main__":
    seed_database()