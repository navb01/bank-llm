"""
FastAPI Main Server for Bank LLM System
Exposes REST API endpoints consumed by the frontend.
Runs on 0.0.0.0 so it's accessible over LAN/Intranet.
"""

import shutil
import logging
import asyncio
import time
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
from threading import Lock

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from config import (
    SERVER_HOST, SERVER_PORT, CORS_ORIGINS,
    CIRCULARS_DIR, BASE_DIR, CHROMA_COLLECTION_INTERNAL, SCRAPE_SOURCES,
    ENABLE_QUERY_LOGGING, QUERY_LOG_FILE, LOG_LEVEL, LOG_FORMAT,
    ENABLE_RATE_LIMITING, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS
)
from document_processor import (
    ingest_document, get_ingestion_stats,
    list_ingested_files, get_collection, get_chroma_client, is_file_already_ingested,
    get_embeddings
)
from rag_engine import ask, get_llm
from web_scraper import run_web_scraping
from learning import learning_manager
from adaptive_learning import adaptive_manager
from database import init_db

# Global state for ingestion lock
ingestion_lock = Lock()
ingestion_in_progress = False

# ─── Logging Setup ────────────────────────────────────────────────────────────

# Create logs directory
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True, parents=True)

# Configure logging to file and console
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOGS_DIR / "main.log"),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# Query logger to file
if ENABLE_QUERY_LOGGING:
    query_logger = logging.getLogger("queries")
    query_handler = logging.FileHandler(QUERY_LOG_FILE)
    query_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    query_logger.addHandler(query_handler)
    query_logger.setLevel(logging.INFO)
else:
    query_logger = None

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Bank LLM API",
    description="Personalized LLM for Bank Staff — Powered by RAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend files
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# ─── Pydantic Models ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None  # For personalization


class ChatResponse(BaseModel):
    answer: str
    sources: list
    chunks_found: int
    timestamp: str
    cached: bool = False  # Whether answer came from cache
    similar_cached: Optional[Dict] = None  # Similar cached answer if available


class DeleteDocRequest(BaseModel):
    filename: str


class FeedbackRequest(BaseModel):
    """User feedback on an answer."""
    query: str
    answer: str
    rating: int  # 1-5
    sources: list = []
    comment: str = ""
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    topic: Optional[str] = None  # Query topic for analytics
    response_time_ms: Optional[float] = None  # For performance tracking
    cached: bool = False  # Whether the answer was from cache


# ─── Rate Limiting ────────────────────────────────────────────────────────────

request_counts = {}  # IP -> [(timestamp, count)]

def rate_limit_key(request: Request):
    """Get rate limit key from request."""
    return request.client.host if request.client else "unknown"

async def check_rate_limit(request: Request):
    """Check if request exceeds rate limit."""
    if not ENABLE_RATE_LIMITING:
        return True
    
    key = rate_limit_key(request)
    now = datetime.now().timestamp()
    
    if key not in request_counts:
        request_counts[key] = []
    
    # Remove old requests outside the window
    request_counts[key] = [
        (ts, cnt) for ts, cnt in request_counts[key]
        if now - ts < RATE_LIMIT_WINDOW_SECONDS
    ]
    
    # Count requests in current window
    total = sum(cnt for _, cnt in request_counts[key])
    
    if total >= RATE_LIMIT_REQUESTS:
        return False
    
    # Add current request
    if request_counts[key]:
        request_counts[key][-1] = (request_counts[key][-1][0], request_counts[key][-1][1] + 1)
    else:
        request_counts[key].append((now, 1))
    
    return True


# ─── In-memory query log ──────────────────────────────────────────────────────
query_log: list[dict] = []


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Serve the frontend."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Bank LLM API is running. Frontend not found."}


@app.get("/admin")
async def admin():
    """Serve the admin panel."""
    admin_file = FRONTEND_DIR / "admin.html"
    if admin_file.exists():
        return FileResponse(str(admin_file))
    raise HTTPException(status_code=404, detail="Admin page not found")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request):
    """
    Main chat endpoint. Receives a query, runs RAG pipeline,
    returns grounded answer with citations.
    Integrates adaptive learning for continuous improvement.
    """
    global ingestion_in_progress
    
    # Rate limiting
    if not await check_rate_limit(req):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 100 requests per 60 seconds."
        )
    
    # Prevent queries during ingestion
    if ingestion_in_progress:
        raise HTTPException(
            status_code=503,
            detail="System is currently ingesting documents. Please wait 30-60 seconds and try again."
        )
    
    if not request.query or len(request.query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query too short")

    query = request.query.strip()
    user_id = request.user_id or "anonymous"
    user_ip = req.client.host if req.client else "unknown"
    logger.info(f"Chat query from {user_id} ({user_ip}): {query[:100]}...")

    start_time = time.time()
    
    try:
        # Check for similar cached answers first
        similar_cached = adaptive_manager.query_clustering.find_similar_cached(query)
        cached = False
        
        if similar_cached:
            # Use cached answer
            answer = similar_cached["answer"]
            sources = similar_cached.get("sources", [])
            chunks_found = len(sources)
            cached = True
            logger.info(f"Serving cached answer with {len(sources)} sources")
        else:
            # Run full RAG pipeline in thread pool executor so FastAPI event loop is not blocked
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, ask, query)
            answer = result["answer"]
            sources = result["sources"]
            chunks_found = result["chunks_found"]
        
        response_time = (time.time() - start_time) * 1000  # ms

        response = ChatResponse(
            answer=answer,
            sources=sources,
            chunks_found=chunks_found,
            timestamp=datetime.now().isoformat(),
            cached=cached,
            similar_cached=None  # Don't echo cached data in response
        )

        # Log query
        query_data = {
            "query": query,
            "answer_length": len(answer),
            "sources_count": len(sources),
            "timestamp": response.timestamp,
            "user_id": user_id,
            "user_ip": user_ip,
            "response_time_ms": response_time,
            "cached": cached,
        }
        query_log.append(query_data)
        
        # Log to file if enabled
        if query_logger:
            query_logger.info(f"Q: {query[:100]} | Sources: {len(sources)} | User: {user_id} | Time: {response_time:.0f}ms | Cached: {cached}")

        return response

    except Exception as e:
        logger.error(f"Chat error from {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/api/ingest/upload")
async def upload_document(
    file: UploadFile = File(...),
):
    """
    Upload a circular (PDF/DOCX/XLSX/TXT) and ingest it into the vector store.
    Ingestion is done synchronously so the user gets immediate feedback.
    """
    global ingestion_in_progress
    
    allowed_extensions = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt"}
    suffix = Path(file.filename).suffix.lower()

    if suffix not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save file to circulars directory
    save_path = CIRCULARS_DIR / file.filename
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    logger.info(f"Saved uploaded file to {save_path}")

    # Check if file is already ingested to prevent duplicates
    if is_file_already_ingested(file.filename):
        logger.info(f"File {file.filename} already ingested, skipping")
        return {
            "status": "skipped",
            "filename": file.filename,
            "message": f"File already ingested previously. No duplicate indexing needed."
        }

    # Mark ingestion as in progress
    with ingestion_lock:
        ingestion_in_progress = True
    
    # Ingest synchronously in thread pool so the user knows if it worked
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, ingest_document, save_path)
        if result.get("status") == "error":
            logger.warning(f"Ingestion failed for {file.filename}: {result.get('message')}")
            return {
                "status": "error",
                "filename": file.filename,
                "message": f"File saved but ingestion failed: {result.get('message', 'Could not extract text from the file')}. "
                           f"The file may be empty, scanned (image-only PDF), or corrupted."
            }

        return {
            "status": "success",
            "filename": file.filename,
            "chunks": result.get("chunks", 0),
            "message": f"File uploaded and ingested successfully! "
                       f"{result.get('chunks', 0)} text chunks indexed and ready for queries."
        }
    except Exception as e:
        logger.error(f"Ingestion error for {file.filename}: {e}")
        return {
            "status": "error",
            "filename": file.filename,
            "message": f"File saved but ingestion encountered an error: {str(e)}"
        }
    finally:
        # Mark ingestion as complete
        with ingestion_lock:
            ingestion_in_progress = False


@app.post("/api/ingest/folder")
async def ingest_folder(background_tasks: BackgroundTasks):
    """
    Ingest all documents in the circulars/ folder.
    Only ingests files that haven't been ingested before.
    """
    global ingestion_in_progress
    
    supported_ext = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt"}
    files = [f for f in CIRCULARS_DIR.glob("**/*") if f.suffix.lower() in supported_ext]

    if not files:
        return {"status": "no_files", "message": "No supported files found in circulars/ folder"}

    # Filter out already ingested files
    files_to_ingest = [f for f in files if not is_file_already_ingested(f.name)]
    
    if not files_to_ingest:
        return {"status": "all_ingested", "message": "All files in circulars/ folder have already been ingested."}
    
    logger.info(f"Found {len(files_to_ingest)} new files to ingest out of {len(files)} total")
    
    with ingestion_lock:
        ingestion_in_progress = True
    
    background_tasks.add_task(_ingest_all, files_to_ingest)

    return {
        "status": "processing",
        "files_found": len(files),
        "message": f"Found {len(files)} files. Ingestion started in background."
    }


@app.post("/api/ingest/reingest")
async def reingest_all(background_tasks: BackgroundTasks):
    """
    Clear the entire vector DB collection and re-ingest all documents fresh.
    This is critical when RAG parameters (chunk size, overlap, etc.) have changed.
    """
    supported_ext = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt"}
    files = [f for f in CIRCULARS_DIR.glob("**/*") if f.suffix.lower() in supported_ext]

    if not files:
        return {"status": "no_files", "message": "No supported files found in circulars/ folder"}

    # Clear the existing collection completely
    try:
        client = get_chroma_client()
        try:
            client.delete_collection(CHROMA_COLLECTION_INTERNAL)
            logger.info("Deleted old collection for clean re-ingestion")
        except Exception:
            pass  # Collection might not exist yet
    except Exception as e:
        logger.warning(f"Could not clear collection: {e}")

    background_tasks.add_task(_ingest_all, files)

    return {
        "status": "processing",
        "files_found": len(files),
        "message": f"Cleared vector DB. Re-ingesting {len(files)} files from scratch in background."
    }


async def _ingest_all(files: list[Path]):
    """Run blocking ingestion in a thread pool to avoid blocking the event loop."""
    global ingestion_in_progress

    loop = asyncio.get_event_loop()
    results = []

    try:
        for f in files:
            try:
                result = await loop.run_in_executor(None, ingest_document, f)
                results.append(result)
                logger.info(f"  Bulk ingest result for {f.name}: {result.get('status')}")
            except Exception as e:
                logger.error(f"  Bulk ingest error for {f.name}: {e}")
                results.append({"status": "error", "file": f.name, "message": str(e)})

        success = sum(1 for r in results if r.get("status") == "success")
        errors = sum(1 for r in results if r.get("status") == "error")
        logger.info(f"Bulk ingestion complete: {success} succeeded, {errors} failed out of {len(results)} files")
    finally:
        # Mark ingestion as complete
        with ingestion_lock:
            ingestion_in_progress = False


@app.post("/api/ingest/web")
async def ingest_web_sources(background_tasks: BackgroundTasks):
    """
    Trigger web scraping from RBI, NABARD, SEBI regulatory websites.
    This runs in background and ingests public circulars into the knowledge base.
    """
    logger.info("Web scraping requested")
    background_tasks.add_task(_run_scraping_task)
    
    return {
        "status": "started",
        "message": "Web scraping started in background. Check /api/scraping/status for progress.",
        "sources_count": len(list(SCRAPE_SOURCES))
    }


# ─── Scraping Status Tracking ────────────────────────────────────────────────
scraping_in_progress = False
last_scrape_result = None


async def _run_scraping_task():
    """Run web scraping in background."""
    global scraping_in_progress, last_scrape_result
    scraping_in_progress = True
    try:
        logger.info("Starting web scraping task...")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_web_scraping, False)
        last_scrape_result = result
        logger.info(f"Web scraping completed: {result['successful_sources']} sources succeeded")
    except Exception as e:
        logger.error(f"Web scraping failed: {e}")
        last_scrape_result = {"status": "error", "error": str(e)}
    finally:
        scraping_in_progress = False


@app.get("/api/scraping/status")
async def get_scraping_status():
    """Get the status of web scraping task."""
    return {
        "in_progress": scraping_in_progress,
        "last_result": last_scrape_result,
        "timestamp": datetime.now().isoformat()
    }


# ─── Self-Learning & Feedback ────────────────────────────────────────────────

@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback on an answer.
    Enables the system to learn and improve over time.
    Integrates both basic learning and adaptive learning.
    """
    try:
        if not 1 <= request.rating <= 5:
            raise HTTPException(status_code=400, detail="Rating must be 1-5")
        
        user_id = request.user_id or "anonymous"
        
        # Record in basic learning system
        learning_manager.process_feedback(
            query=request.query,
            answer=request.answer,
            rating=request.rating,
            sources=request.sources,
            comment=request.comment,
            user_ip="unknown"
        )
        
        # Record in adaptive learning system
        adaptive_manager.process_interaction(
            user_id=user_id,
            query=request.query,
            answer=request.answer,
            rating=request.rating,
            sources=request.sources,
            response_time_ms=request.response_time_ms or 0,
            topic=request.topic or "general",
            cached=request.cached
        )
        
        logger.info(f"Feedback submitted: user={user_id}, rating={request.rating}, query={request.query[:50]}...")
        
        return {
            "status": "recorded",
            "message": "Thank you! Your feedback helps us improve.",
            "rating": request.rating,
            "timestamp": datetime.now().isoformat(),
            "learning_active": True
        }
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {str(e)}")


@app.get("/api/learning/dashboard")
async def get_learning_dashboard():
    """
    Get learning analytics dashboard.
    Shows system performance, feedback stats, and improvement suggestions.
    """
    try:
        dashboard = learning_manager.get_dashboard_data()
        return {
            "status": "success",
            "data": dashboard,
            "timestamp": datetime.now().isoformat(),
            "learning_enabled": True
        }
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/learning/stats")
async def get_learning_stats():
    """Get aggregated learning statistics."""
    try:
        stats = learning_manager.analytics.compute_stats()
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/learning/recommendations")
async def get_recommendations():
    """Get AI recommendations for system improvement."""
    try:
        recommendations = learning_manager.analytics.get_improvement_recommendations()
        optimizations = learning_manager.adaptive_rag.get_current_insights()
        
        return {
            "status": "success",
            "recommendations": recommendations,
            "optimizations": optimizations,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Advanced Adaptive Learning Endpoints ────────────────────────────────────

@app.get("/api/learning/adaptive/dashboard")
async def get_adaptive_dashboard():
    """Get comprehensive adaptive learning dashboard."""
    try:
        dashboard = adaptive_manager.get_learning_dashboard()
        return {
            "status": "success",
            "data": dashboard,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Adaptive dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/learning/adaptive/user-profile/{user_id}")
async def get_user_profile(user_id: str):
    """Get personalized user profile and preferences."""
    try:
        profile = adaptive_manager.user_profiles.get_user_profile(user_id)
        params = adaptive_manager.user_profiles.get_personalized_params(user_id)
        
        return {
            "status": "success",
            "user_id": user_id,
            "profile": profile,
            "personalized_params": params,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"User profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/learning/adaptive/cache-stats")
async def get_cache_statistics():
    """Get query cache performance statistics."""
    try:
        stats = adaptive_manager.query_clustering.get_cache_stats()
        return {
            "status": "success",
            "cache_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learning/adaptive/suggest-improvements")
async def suggest_query_improvements(query: str):
    """
    Suggest improvements for a query based on learned patterns.
    Returns rewrite suggestions and similar cached answers.
    """
    try:
        suggestions = adaptive_manager.suggest_improvements(query)
        return {
            "status": "success",
            "query": query,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Suggest improvements error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/learning/adaptive/performance/{topic}")
async def get_topic_performance(topic: str = "general"):
    """Get performance metrics for a specific query topic."""
    try:
        analysis = adaptive_manager.performance_metrics.get_topic_analysis(topic)
        return {
            "status": "success",
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Topic performance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/learning/adaptive/optimization-insights")
async def get_optimization_insights():
    """Get insights for system optimization based on performance data."""
    try:
        insights = adaptive_manager.performance_metrics.get_optimization_insights()
        return {
            "status": "success",
            "insights": insights,
            "count": len(insights),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Optimization insights error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/learning/adaptive/all-users-stats")
async def get_all_users_stats():
    """Get aggregated statistics across all users."""
    try:
        stats = adaptive_manager.user_profiles.get_all_user_stats()
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"All users stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents/{filename}")
async def delete_document(filename: str):
    """
    Remove a document from the vector store (and optionally the circulars folder).
    """
    try:
        collection = get_collection(CHROMA_COLLECTION_INTERNAL)
        existing = collection.get(where={"filename": filename})
        if not existing["ids"]:
            raise HTTPException(status_code=404, detail=f"Document '{filename}' not found in knowledge base")

        collection.delete(ids=existing["ids"])

        # Optionally delete the file
        file_path = CIRCULARS_DIR / filename
        if file_path.exists():
            file_path.unlink()

        return {
            "status": "deleted",
            "filename": filename,
            "chunks_removed": len(existing["ids"])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
async def list_documents():
    """List all ingested documents with their metadata."""
    internal = list_ingested_files(CHROMA_COLLECTION_INTERNAL)
    external = list_ingested_files("regulatory_docs")
    return {
        "internal_circulars": internal,
        "regulatory_docs": external,
    }


@app.get("/api/status")
async def get_status():
    """System health check and stats."""
    stats = get_ingestion_stats()
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "vector_db": stats,
        "queries_served": len(query_log),
        "ollama_model": "llama3.2",
        "server": f"http://{SERVER_HOST}:{SERVER_PORT}",
    }


@app.get("/api/logs")
async def get_query_logs():
    """Return recent query logs (last 50)."""
    return {"logs": query_log[-50:]}


# ─── Startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("  Bank LLM System Starting Up")
    logger.info(f"  Server: http://0.0.0.0:{SERVER_PORT}")
    logger.info(f"  Circulars Dir: {CIRCULARS_DIR}")
    logger.info(f"  Vector DB: {BASE_DIR / 'vector_db'}")
    logger.info("=" * 60)

    # Initialize database
    try:
        init_db()
        logger.info("  ✓ Database initialized")
    except Exception as e:
        logger.error(f"  ✗ Database initialization failed: {e}")

    # Pre-warm singletons (ChromaDB client, Embedder, LLM)
    try:
        get_chroma_client()
        get_embeddings()
        get_llm()
        logger.info("  ✓ ChromaDB and Ollama singletons initialized")
    except Exception as e:
        logger.warning(f"  ! Pre-warming warning: {e}")

    # Log vector DB stats
    stats = get_ingestion_stats()
    for col, count in stats.items():
        logger.info(f"  Vector DB [{col}]: {count} chunks")


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=False,
        log_level="info",
    )
