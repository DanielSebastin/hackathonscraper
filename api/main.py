from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from scraper.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler(background=True)   # starts the 12-hr pipeline in background
    yield

app = FastAPI(title="Hackathon Semantic Search API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {"message": "API is live! Send a POST request to /search"}