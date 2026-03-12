from models.embedding_model import get_embedding
from database.qdrant_db import search_qdrant

def process_search(query_text: str, limit: int):
    vector = get_embedding(query_text)
    raw_results = search_qdrant(vector, query_text, limit)
    
    formatted_data = []
    for hit in raw_results:
        payload = hit.payload
        formatted_data.append({
            "title": payload.get("title"),
            "date": payload.get("date"),
            "end_date": payload.get("end_date"),
            "registration_deadline": payload.get("registration_deadline"),
            "location": payload.get("location"),
            "type": payload.get("type"),
            "registration_url": payload.get("registration_url"),
            "visit_url": payload.get("visit_url"),
            "prize": payload.get("prize"),
            "fee": payload.get("fee"),
            "team_size": payload.get("team_size"),
            "domains": payload.get("domains", []),
            "problem_statements": payload.get("problem_statements", []),
            "description": payload.get("clean_description"),
            "score": round(hit.score, 2)
        })
        
    return formatted_data