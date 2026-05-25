"""
Configuration for Bank LLM System
All settings in one place — edit here to customize.
"""

import os
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
CIRCULARS_DIR = BASE_DIR / "circulars"
VECTOR_DB_DIR = BASE_DIR / "vector_db"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for d in [CIRCULARS_DIR, VECTOR_DB_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Ollama / LLM Settings ────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "llama3.2"          # Change to "mistral" or "llama3.1:8b" etc.
EMBED_MODEL = "nomic-embed-text" # Local embedding model via Ollama

# ─── ChromaDB Settings ────────────────────────────────────────────────────────
CHROMA_COLLECTION_INTERNAL = "bank_circulars"    # Internal bank circulars
CHROMA_COLLECTION_EXTERNAL = "regulatory_docs"   # RBI / NABARD / SEBI docs

# ─── RAG Settings ─────────────────────────────────────────────────────────────
CHUNK_SIZE = 1000           # Characters per chunk (larger = more context per chunk)
CHUNK_OVERLAP = 200         # Overlap between chunks (prevents splitting key info)
TOP_K_RESULTS = 8           # Number of chunks to retrieve per query
MIN_SIMILARITY_SCORE = 0.10 # Low threshold — let more chunks through for LLM to evaluate

# ─── Security & Rate Limiting ────────────────────────────────────────────────
ENABLE_RATE_LIMITING = True
RATE_LIMIT_REQUESTS = 100        # Requests per window
RATE_LIMIT_WINDOW_SECONDS = 60   # Time window in seconds

# IP Whitelist for admin panel (empty = allow all on LAN)
ADMIN_IP_WHITELIST = []  # Example: ["192.168.1.*", "127.0.0.1"]

# ─── Logging & Monitoring ────────────────────────────────────────────────────
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
ENABLE_QUERY_LOGGING = True  # Log all queries to file
QUERY_LOG_FILE = LOGS_DIR / "queries.log"
SCRAPE_LOG_FILE = LOGS_DIR / "scraping.log"

# ─── Performance Optimization ────────────────────────────────────────────────
ENABLE_QUERY_CACHING = True
CACHE_TTL_SECONDS = 300  # Cache query results for 5 minutes
MAX_WORKERS = 4  # Thread pool size for parallel tasks

# ─── Web Scraping (Secondary Learning) ────────────────────────────────────────
# Configure RBI, NABARD, SEBI sources for web scraping
SCRAPE_SOURCES = [
    {
        "name": "RBI - Notifications & Circulars",
        "url": "https://www.rbi.org.in/scripts/NotificationUser.aspx",
        "category": "RBI",
    },
    {
        "name": "RBI - Master Circulars",
        "url": "https://www.rbi.org.in/scripts/BS_ViewMasterCircular.aspx",
        "category": "RBI",
    },
    {
        "name": "NABARD - Circulars & Guidelines",
        "url": "https://www.nabard.org/scripts/Circularscript.php",
        "category": "NABARD",
    },
    {
        "name": "SEBI - Circulars",
        "url": "https://www.sebi.gov.in/sebiweb/other/OtherPage.html?page_id=714",
        "category": "SEBI",
    },
    {
        "name": "SEBI - Notifications",
        "url": "https://www.sebi.gov.in/sebiweb/other/OtherPage.html?page_id=715",
        "category": "SEBI",
    },
]

# Web scraping schedule (run every N hours) - 0 to disable
SCRAPE_SCHEDULE_HOURS = 24

# ─── System Prompt (Anti-Hallucination) ───────────────────────────────────────
SYSTEM_PROMPT = """You are BankAssist, an AI assistant for bank staff. You are trained on internal bank circulars and regulatory documents from RBI, NABARD, and SEBI.

CRITICAL RULES — YOU MUST FOLLOW THESE WITHOUT EXCEPTION:
1. Answer ONLY using information from the provided context documents below.
2. If the context does not contain sufficient information to answer the question, respond with: "I don't have information about this topic in the available circulars and documents. Please consult the relevant department or check the original source."
3. NEVER guess, infer, or make up information that is not explicitly in the context.
4. ALWAYS cite the source: include the Circular Reference Number, Date, and Issuing Authority if available.
5. If multiple circulars are relevant, cite all of them.
6. Be precise and factual. Bank data is sensitive and critical.
7. If a circular has been superseded by a newer one in the context, mention that.

FORMAT YOUR RESPONSE AS:
- Direct answer to the query
- Source: [Circular/Document Reference] | Date: [Date] | Issued by: [Authority]

Context Documents:
{context}

Remember: If the answer is not in the context above, say so clearly. Do not fabricate information."""

# ─── Server Configuration ────────────────────────────────────────────────────
SERVER_HOST = "0.0.0.0"  # Listen on all interfaces (accessible over LAN)
SERVER_PORT = 8000
CORS_ORIGINS = ["*"]  # Allow all origins on LAN
