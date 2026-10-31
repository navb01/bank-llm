"""
Document Processor for Bank LLM System (Optimized Singletons)
"""

import re
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

import chromadb
from chromadb.config import Settings

import pypdf
import docx
import openpyxl

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings

try:
    import pytesseract
    pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except ImportError:
    pytesseract = None

from config import (
    VECTOR_DB_DIR,
    CHROMA_COLLECTION_INTERNAL,
    EMBED_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    OLLAMA_BASE_URL,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Global Singletons (Initialized Once, Kept in Memory) ────────────────────
_chroma_client = None
_embedder_instance = None


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=str(VECTOR_DB_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
    return _chroma_client


def get_collection(collection_name: str):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )


def get_embeddings():
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = OllamaEmbeddings(
            model=EMBED_MODEL,
            base_url=OLLAMA_BASE_URL,
            keep_alive=-1  # Keeps embedder loaded in Ollama RAM permanently
        )
    return _embedder_instance


# ─── Metadata Extraction, Parsers, and Ingestion (Same as before) ─────────────
# Keep extract_circular_metadata, parse_pdf, parse_docx, parse_xlsx, parse_txt, 
# parse_document, ingest_document, ingest_text, get_ingestion_stats, list_ingested_files 
# exactly as you wrote them below this point.
