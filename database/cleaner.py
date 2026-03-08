def clean_event_description(text: str) -> str:
    if not text:
        return ""
        
    cleaned = text
    cutoff_phrases = ["Related Links:", "Online FDP |", "Participate in Events"]
    for phrase in cutoff_phrases:
        if phrase in cleaned:
            cleaned = cleaned.split(phrase)[0]

    top_cutoff = "About Event"
    if top_cutoff in cleaned:
        cleaned = cleaned.split(top_cutoff)[-1]

    return cleaned.strip()