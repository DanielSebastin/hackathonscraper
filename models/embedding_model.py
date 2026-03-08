from sentence_transformers import SentenceTransformer
from pydantic import BaseModel

# 1. Define what the frontend will send us
class SearchQuery(BaseModel):
    text: str
    limit: int = 5

# 2. Load the AI Model once globally so it's lightning fast
print("Loading AI Embedding Model...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text: str) -> list:
    """Converts a text string into a mathematical vector array."""
    return embedder.encode(text).tolist()