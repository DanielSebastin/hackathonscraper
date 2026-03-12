import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchText

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "hackathons"

# Initialize the client properly
print("Connecting to Qdrant Cloud...")
db = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def search_qdrant(query_vector: list, query_text: str = None, limit: int = 5):
    """Hits the Qdrant database with a hybrid approach if text is provided."""
    
    # If we have query_text, boost results matching key fields (Hybrid Search)
    search_filter = None
    if query_text:
        search_filter = Filter(
            should=[
                FieldCondition(key="title", match=MatchText(text=query_text)),
                FieldCondition(key="domains", match=MatchText(text=query_text)),
                FieldCondition(key="clean_description", match=MatchText(text=query_text)),
            ]
        )

    results = db.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=search_filter,
        limit=limit,
        score_threshold=0.35 # Balanced for hybrid and semantic relevance
    ).points
    return results

def get_all_points(limit: int = 500):
    """Fetches points from the collection in a stable order for browsing."""
    results, _ = db.scroll(
        collection_name=COLLECTION_NAME,
        limit=limit,
        with_payload=True,
        with_vectors=False
    )
    return results