# Hackathon Discovery & Semantic Search System
### Design Document — v1.0

---

## 1. Problem Statement

Hackathons are among the most powerful learning and networking opportunities for students and developers. Yet discovering them remains frustratingly manual. Events are scattered across platforms like **Knowafest**, **Devpost**, **MLH**, and **Unstop**, each with its own interface and search logic.

Traditional search on these platforms is **keyword-based and rigid**. A search for *"AI hackathons"* may completely miss events labeled as *"Machine Learning Competition"*, *"Data Science Challenge"*, or *"Agentic AI Ideathon"* — even though they are semantically identical to what the user wants.

The result: students and developers **miss opportunities** they would have been excited about, simply because they used a slightly different search term or didn't know which platform to check.

**Core Problems:**
- No single place to discover all hackathons
- Keyword search fails to capture semantic intent
- No automatic updates — listings go stale quickly
- No personalization or recommendation layer

---

## 2. Solution

### Non-Technical Solution

We are building a **centralized hackathon discovery platform** that:

| Feature | Description |
|---|---|
| **Unified Search** | One search bar to find hackathons across all aggregated platforms |
| **Semantic Understanding** | Understands the *intent* behind queries, not just exact keywords |
| **Automatic Updates** | Data is refreshed automatically on a schedule — no manual effort |
| **Topic/Location/Time Filters** | Discover hackathons by theme, city, or date range |
| **Intelligent Recommendations** | Surfaces events the user didn't know to search for |

A user can simply type *"AI hackathons in Chennai this month"* and receive relevant results even if the events use entirely different terminology.

---

### Technical Solution

The system is built around three pillars:

1. **Data Ingestion Pipeline** — A scheduled web scraper collects and structures hackathon listings from supported platforms.
2. **Semantic Search Engine** — Hackathon descriptions are converted into high-dimensional vector embeddings. Queries are matched by vector similarity, not keyword overlap.
3. **REST API + Frontend** — A FastAPI backend serves search results to any frontend or third-party client.

**Optional Enhancement:** An LLM reasoning layer (Mistral) can summarize events, extract tags, and generate personalized recommendations.

---

## 3. Workflow

### User Workflow

```
1. User opens the Hackathon Search Application
        │
2. User types a natural language query
   e.g. "AI hackathons in Chennai this month"
        │
3. Backend receives the query via POST /search
        │
4. Query is converted into a 384-dimensional vector
   using the sentence-transformers embedding model
        │
5. Vector similarity search runs on the Qdrant database
        │
6. Top-N most semantically similar hackathons are returned
        │
7. Results are displayed with title, date, location, and link
        │
8. User clicks a registration link to view the full event
```

---

### Internal System Workflow (Data Pipeline)

```
1. APScheduler triggers the scraper every 12–24 hours
        │
2. Playwright scrapes Knowafest (and future platforms)
        │
3. Raw HTML is parsed into structured JSON records:
   { title, date, location, type, description, url }
        │
4. Descriptions are cleaned (HTML stripped, normalized)
        │
5. Each hackathon's text is embedded into a vector:
   "Title: X. Type: Y. Location: Z. Details: ..."
        │
6. Vectors + payloads are upserted into Qdrant Cloud
        │
7. API is immediately ready to serve updated results
```

---

## 4. Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                   USER / BROWSER                    │
└─────────────────────┬───────────────────────────────┘
                      │  HTTP request
                      ▼
┌─────────────────────────────────────────────────────┐
│            Frontend / Search Interface              │
│         (HTML + JS  or  React application)          │
└─────────────────────┬───────────────────────────────┘
                      │  POST /search  { "text": "..." }
                      ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (api/)                 │
│  routes.py → search_service.py                      │
└──────────┬──────────────────────┬───────────────────┘
           │                      │
           ▼                      ▼
┌──────────────────┐   ┌──────────────────────────────┐
│  Embedding Model │   │   Qdrant Vector Database     │
│ (all-MiniLM-L6)  │   │       (Qdrant Cloud)         │
│ query → vector   │──▶│  vector similarity search    │
└──────────────────┘   └──────────────────────────────┘

─────────────────── DATA INGESTION PIPELINE ──────────────────

┌──────────────────────────────────────────────────────┐
│           APScheduler / Cron (every 12h)             │
└─────────────────────┬────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│          Web Scraper — Playwright (scraper/)         │
│       Knowafest → raw HTML → structured JSON        │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│        Data Cleaner (database/cleaner.py)           │
│     Strip HTML, normalize whitespace, deduplicate   │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│     Embedding Model → Qdrant Uploader (database/)   │
│   Text → 384-dim vector → upsert to Qdrant Cloud   │
└─────────────────────────────────────────────────────┘
```

### Component Descriptions

| Component | Role |
|---|---|
| **Frontend** | Provides the search UI. Sends queries to FastAPI and renders results. |
| **FastAPI (api/)** | REST API backbone. Exposes `POST /search`. Orchestrates embedding + retrieval. |
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` — converts text to 384-dim vectors. Loaded once at startup for speed. |
| **Qdrant Cloud** | Managed vector database. Stores hackathon vectors and metadata payloads. Handles ANN (Approximate Nearest Neighbour) search. |
| **Playwright Scraper** | Headless browser automation. Handles JavaScript-rendered pages and pagination. |
| **Data Cleaner** | Strips HTML tags, normalizes text, removes noise before embedding. |
| **APScheduler** | Triggers the scraping pipeline periodically without manual intervention. |

---

## 5. Technology Stack

| Category | Tool | Why |
|---|---|---|
| **Scraping** | Playwright | Handles JS-rendered pages that `requests` cannot. Robust for SPAs and dynamic content. |
| **Backend** | FastAPI | Async Python framework. Auto-generates OpenAPI docs. Fast and production-ready. |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) | Lightweight (80MB), fast, high-quality 384-dim sentence embeddings. Runs on CPU. |
| **Vector Search** | Qdrant Cloud | Purpose-built vector DB. Managed cloud offering. Supports filtering + ANN search. |
| **Optional LLM** | Mistral (via API) | Open-weight model. Can summarize event descriptions, extract tags, or rank results with reasoning. |
| **Scheduler** | APScheduler | Pure Python. Embeds into the application without needing external cron infrastructure. |
| **Deployment** | AWS EC2 | Full control over environment. Can host both the API and the scheduler on one instance. |

---

## 6. Folder Structure

```
HackathonProject/
│
├── api/                        # FastAPI REST backend
│   ├── main.py                 #   App factory, CORS, router registration
│   ├── routes.py               #   Endpoint definitions (POST /search)
│   └── search_service.py       #   Business logic: embed query → search Qdrant → format results
│
├── database/                   # Data layer
│   ├── qdrant_client.py        #   Qdrant connection + search_qdrant() function
│   ├── uploader.py             #   Seeds Qdrant from raw_events.json
│   └── cleaner.py              #   Text normalization and HTML stripping
│
├── models/                     # ML model layer
│   └── embedding_model.py      #   Loads sentence-transformers model; exposes get_embedding()
│
├── scraper/                    # Data collection pipeline
│   ├── scraper.py              #   Playwright-based scraper for Knowafest
│   ├── parser.py               #   Parses raw HTML into structured dicts
│   └── scheduler.py            #   APScheduler job definitions (periodic trigger)
│
├── data/                       # Raw and processed data storage
│   └── raw_events.json         #   Scraped hackathon records (source of truth)
│
├── utils/                      # Shared helpers
│   └── helpers.py              #   Utility functions (date parsing, deduplication, etc.)
│
├── .env                        # Environment secrets (QDRANT_URL, QDRANT_API_KEY)
├── requirements.txt            # Python dependencies
├── DESIGN_DOCUMENT.md          # This document
└── README.md                   # Quick-start guide
```

---

## 7. Future Improvements

| Improvement | Description |
|---|---|
| **Multi-Platform Scraping** | Extend scrapers to cover Devpost, Unstop, MLH, HackerEarth, and Hack2Skill |
| **Personalized Recommendations** | Track user search history to surface relevant upcoming events proactively |
| **Location-Aware Search** | Integrate geolocation to automatically filter events near the user's city |
| **Automated Alerts** | Email or push notifications when a new hackathon matching a saved query is found |
| **LLM Summarization** | Use Mistral to auto-generate one-paragraph summaries of each hackathon |
| **LLM Tagging** | Auto-tag events with themes (AI, Web3, Healthcare, etc.) for faceted filtering |
| **Team Formation** | Let users post skills and find teammates for upcoming hackathons |
| **Deadline Tracker** | Dashboard view showing registration deadlines sorted by urgency |
| **Offline FAISS Fallback** | Local FAISS index as a backup when Qdrant Cloud is unreachable |

---

*Document prepared for Hackathon Project Presentation — March 2026*
