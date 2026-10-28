"""Application configuration."""

from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
PUBLIC_DIR = ROOT_DIR / "public"

MODEL_ID = os.getenv("STYLESHIFT_MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct")
HOST = os.getenv("STYLESHIFT_HOST", "127.0.0.1")
PORT = int(os.getenv("STYLESHIFT_PORT", "3000"))
MAX_TEXT_LENGTH = int(os.getenv("STYLESHIFT_MAX_TEXT_LENGTH", "2000"))
