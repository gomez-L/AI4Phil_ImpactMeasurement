"""
Centralised configuration — reads from environment / .env file.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ─── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ─── LLM ───────────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
MODEL_NAME: str = os.getenv("MODEL_NAME", "gemma-4-31b-it")
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))

# ─── LangFuse ──────────────────────────────────────────────────────────────────
LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
LANGFUSE_ENABLED: bool = os.getenv("LANGFUSE_ENABLED", "true").strip().lower() in {
	"1",
	"true",
	"yes",
	"on",
} and bool(LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)

# ─── Vector Store ──────────────────────────────────────────────────────────────
CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", str(DATA_DIR / "chroma_db"))
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # local HuggingFace model — no API key needed

# ─── Workshop Pricing (CHF) ────────────────────────────────────────────────────
ONSITE_PRICE_CHF: float = float(os.getenv("ONSITE_PRICE_CHF", "15.0"))
ONLINE_PRICE_CHF: float = float(os.getenv("ONLINE_PRICE_CHF", "5.0"))
