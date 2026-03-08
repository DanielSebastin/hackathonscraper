"""
helpers.py — Shared utility functions used across the project.
"""

import json
import os
import re
from datetime import datetime


# ─────────────────────────────────────────────
#  File I/O helpers
# ─────────────────────────────────────────────

def load_json(filepath: str) -> list | dict:
    """Load a JSON file and return its contents."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: list | dict, filepath: str) -> None:
    """Save data to a JSON file with pretty formatting."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ─────────────────────────────────────────────
#  Deduplication helpers
# ─────────────────────────────────────────────

def deduplicate_events(events: list) -> list:
    """
    Remove duplicate events by title (case-insensitive).
    Keeps the first occurrence.
    """
    seen_titles = set()
    unique = []
    for event in events:
        normalized = event.get("title", "").strip().lower()
        if normalized and normalized not in seen_titles:
            seen_titles.add(normalized)
            unique.append(event)
    return unique


def merge_events(existing: list, new_events: list) -> list:
    """
    Merge two event lists. New events are appended only if their title
    doesn't already exist in the existing list.
    Returns the merged, deduplicated list.
    """
    combined = existing + new_events
    return deduplicate_events(combined)


# ─────────────────────────────────────────────
#  Text helpers
# ─────────────────────────────────────────────

def strip_html(text: str) -> str:
    """Remove all HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", text).strip()


def normalize_whitespace(text: str) -> str:
    """Replace multiple spaces/newlines with a single space."""
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, max_chars: int = 300) -> str:
    """Truncate text to a max character length, appending ellipsis if needed."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


# ─────────────────────────────────────────────
#  Date helpers
# ─────────────────────────────────────────────

def is_future_event(date_str: str) -> bool:
    """
    Returns True if the given date string represents a future date.
    Falls back to True if parsing fails (better to show than hide).
    """
    formats = ["%d %b %Y", "%d-%b-%Y", "%B %d, %Y", "%d/%m/%Y"]
    for fmt in formats:
        try:
            event_date = datetime.strptime(date_str.strip(), fmt)
            return event_date >= datetime.now()
        except ValueError:
            continue
    return True  # Assume future if we can't parse


def filter_future_events(events: list) -> list:
    """Filter event list to only include upcoming events."""
    return [e for e in events if is_future_event(e.get("date", ""))]


# ─────────────────────────────────────────────
#  Search result helpers
# ─────────────────────────────────────────────

def format_context_for_llm(results: list) -> str:
    """
    Formats search results into a clean plain-text block
    that can be passed as context to a local LLM.
    """
    if not results:
        return "No relevant hackathons were found."

    lines = ["Here are the most relevant hackathons found:\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r.get('title', 'N/A')}")
        lines.append(f"   Date: {r.get('date', 'N/A')}")
        lines.append(f"   Location: {r.get('location', 'N/A')}")
        lines.append(f"   Type: {r.get('type', 'N/A')}")
        if r.get("description"):
            lines.append(f"   About: {truncate(r['description'], 250)}")
        if r.get("registration_url"):
            lines.append(f"   Register: {r['registration_url']}")
        lines.append("")  # blank line between events

    return "\n".join(lines)
