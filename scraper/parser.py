"""
parser.py — Structured field extractor for raw scraped hackathon text.
Helps clean and normalize data before embedding.
"""

import re
from datetime import datetime


def parse_date(raw_date: str) -> str:
    """
    Tries to normalize a raw date string into a consistent format.
    Returns the original string if parsing fails.
    """
    raw_date = raw_date.strip()
    formats = ["%d %b %Y", "%d-%b-%Y", "%B %d, %Y", "%d/%m/%Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(raw_date, fmt).strftime("%d %b %Y")
        except ValueError:
            continue
    return raw_date  # Return as-is if no format matched


def extract_prize(description: str) -> str | None:
    """
    Scans the description for prize/reward mentions and extracts the first hit.
    """
    patterns = [
        r"prize[s]?\s*[:\-]?\s*([\w\s,\.]+)",
        r"reward[s]?\s*[:\-]?\s*([\w\s,\.]+)",
        r"cash prize[s]?\s*[:\-]?\s*([\w\s,\.]+)",
        r"₹\s?[\d,]+",
        r"\$\s?[\d,]+",
        r"INR\s?[\d,]+",
    ]
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def extract_fee(description: str) -> str | None:
    """
    Looks for registration fee mentions in the description.
    """
    fee_patterns = [
        r"registr(?:ation)?\s*fee[s]?\s*[:\-]?\s*([\w\s₹\$\.]+)",
        r"entry fee[s]?\s*[:\-]?\s*([\w\s₹\$\.]+)",
        r"free\s*(of\s*cost|registration)",
        r"no\s*(registration\s*)?fee",
    ]
    for pattern in fee_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None

def extract_registration_deadline(description: str) -> str | None:
    patterns = [
        r"(?:last\s*date|deadline|apply\s*by|register\s*by)[^:\r\n]*[:\-]?\s*(\d{1,2}(?:st|nd|rd|th)?\s*[a-zA-Z]+\s*\d{4})",
        r"(?:last\s*date|deadline|apply\s*by|register\s*by)[^:\r\n]*[:\-]?\s*(\d{1,2}(?:st|nd|rd|th)?\s*[a-zA-Z]+)",
        r"(?:last\s*date|deadline)[^:\r\n]*[:\-]?\s*(\d{2}[-/]\d{2}[-/]\d{2,4})"
    ]
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if len(val) > 4: return val
    return None

def extract_end_date(description: str) -> str | None:
    patterns = [
        r"(?:end\s*date|concludes\s*on)[^:\r\n]*[:\-]?\s*(\d{1,2}(?:st|nd|rd|th)?\s*[a-zA-Z]+\s*\d{4})",
        r"(?:end\s*date|concludes\s*on)[^:\r\n]*[:\-]?\s*(\d{1,2}(?:st|nd|rd|th)?\s*[a-zA-Z]+)",
        r"(?:end\s*date)[^:\r\n]*[:\-]?\s*(\d{2}[-/]\d{2}[-/]\d{2,4})"
    ]
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if len(val) > 4: return val
    return None

def extract_domains(description: str) -> list[str]:
    # Look for lists under themes/domains
    match = re.search(r"(?:Themes|Domains|Tracks|Focus Areas)[\s\S]*?(?:\n\n|\Z)", description, re.IGNORECASE)
    if not match:
        return []
        
    block = match.group(0)
    lines = block.split('\n')
    domains = []
    for line in lines[1:]: # skip the header
        line = line.strip()
        if not line: continue
        # strip bullets
        clean_line = re.sub(r'^[\-\*\•\d\.]+\s*', '', line).strip()
        if 3 < len(clean_line) < 50:
            domains.append(clean_line)
            if len(domains) >= 5: break # limit
            
    return domains

def extract_problem_statements(description: str) -> list[str]:
    match = re.search(r"(?:Problem Statements)[\s\S]*?(?:\n\n|\Z)", description, re.IGNORECASE)
    if not match:
        return []
        
    block = match.group(0)
    lines = block.split('\n')
    statements = []
    for line in lines[1:]: # skip the header
        line = line.strip()
        if not line: continue
        # strip bullets
        clean_line = re.sub(r'^[\-\*\•\d\.]+\s*', '', line).strip()
        if len(clean_line) > 10:
            statements.append(clean_line)
            if len(statements) >= 5: break
            
    return statements


def extract_team_size(description: str) -> str | None:
    """
    Looks for team size specifications in the description.
    """
    patterns = [
        r"team\s*(?:size|of)\s*[:\-]?\s*(\d+\s*(?:to|-)\s*\d+|\d+)",
        r"(\d+)\s*(?:to|-)\s*(\d+)\s*members?",
        r"(\d+)\s*members?\s*per\s*team",
    ]
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def parse_event(raw_event: dict) -> dict:
    """
    Takes a raw scraped event dict and returns a clean, enriched version.
    """
    title = raw_event.get("title", "").strip()
    description = raw_event.get("description", "")

    return {
        "title": title,
        "date": parse_date(raw_event.get("date", "")),
        "type": raw_event.get("type", "").strip(),
        "location": raw_event.get("location", "").strip(),
        "registration_url": raw_event.get("registration_url"),
        "description": description,
        # Extracted enrichment fields
        "prize": extract_prize(description),
        "fee": extract_fee(description),
        "team_size": extract_team_size(description),
        "registration_deadline": extract_registration_deadline(description),
        "end_date": extract_end_date(description),
        "domains": extract_domains(description),
        "problem_statements": extract_problem_statements(description)
    }
