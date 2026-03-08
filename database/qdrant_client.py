import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "hackathons"

# Initialize the client properly
print("Connecting to Qdrant Cloud...")
db = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def search_qdrant(query_vector: list, limit: int = 5):
    """Hits the Qdrant database with a vector and returns the raw hits."""
    results = db.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit
    ).points
    return results