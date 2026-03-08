import json
import os
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from database.qdrant_client import db, COLLECTION_NAME
from models.embedding_model import get_embedding
from database.cleaner import clean_event_description
from scraper.parser import parse_event

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw_events.json')

def seed_database():
    print(f"Setting up Qdrant collection: {COLLECTION_NAME}...")
    db.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    print(f"Reading data from {DATA_PATH}...")
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        events = json.load(f)

    points = []
    for idx, raw_event in enumerate(events):
        event = parse_event(raw_event)
        clean_desc = clean_event_description(event.get("description", ""))
        vector_text = f"Title: {event['title']}. Type: {event['type']}. Location: {event['location']}. Details: {clean_desc}"
        
        print(f"  -> Embedding: {event['title'][:30]}...")
        vector = get_embedding(vector_text)

        payload = {
            "title": event.get("title"),
            "date": event.get("date"),
            "type": event.get("type"),
            "location": event.get("location"),
            "registration_url": event.get("registration_url"),
            "clean_description": clean_desc,
            "prize": event.get("prize"),
            "fee": event.get("fee"),
            "team_size": event.get("team_size"),
            "registration_deadline": event.get("registration_deadline"),
            "end_date": event.get("end_date"),
            "domains": event.get("domains"),
            "problem_statements": event.get("problem_statements")
        }

        points.append(PointStruct(id=idx + 1, vector=vector, payload=payload))

    print("Blasting vectors to Qdrant Cloud...")
    db.upsert(collection_name=COLLECTION_NAME, points=points)
    print("Qdrant database is fully loaded.")

if __name__ == "__main__":
    seed_database()