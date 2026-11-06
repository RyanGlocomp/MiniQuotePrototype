"""Settings, read from environment variables only.

Swapping Ollama for vLLM or a NIM (milestone M6) changes these values, never code.
"""
import os
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "not-needed")
TEXT_MODEL = os.getenv("TEXT_MODEL", "qwen3.8:27b")
VISION_MODEL = os.getenv("VISION_MODEL", "qwen3-vl:8b")

JOBS_DIR = Path(os.getenv("JOBS_DIR", ROOT / "jobs"))
TEMPLATES_DIR = Path(os.getenv("TEMPLATES_DIR", ROOT / "templates"))
AUDIT_DB = Path(os.getenv("AUDIT_DB", ROOT / "jobs" / "audit.db"))

# Placeholder business rules for the mini build. The full build replaces these
# with the signed-off "approved method" and SST rule (see design doc, open questions).
MARKUP = Decimal(os.getenv("MARKUP", "0.20"))
TAX_RATE = Decimal(os.getenv("TAX_RATE", "0.08"))
