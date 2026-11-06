"""FastAPI entry point. M0: /health and /templates. Job routes arrive in M4."""
import shutil

import httpx
from fastapi import FastAPI

from . import config
from .registry import load_registry

app = FastAPI(title="Mini Quote Builder API", version="0.1.0")


def _llm_status() -> dict:
    try:
        r = httpx.get(f"{config.LLM_BASE_URL}/models", timeout=3,
                      headers={"Authorization": f"Bearer {config.LLM_API_KEY}"})
        r.raise_for_status()
        served = {m.get("id") for m in r.json().get("data", [])}
        wanted = {config.TEXT_MODEL, config.VISION_MODEL}
        return {"ok": wanted <= served, "base_url": config.LLM_BASE_URL,
                "missing_models": sorted(wanted - served)}
    except Exception as e:  # report, don't crash: health must always answer
        return {"ok": False, "base_url": config.LLM_BASE_URL, "error": type(e).__name__}


@app.get("/health")
def health():
    try:
        templates = {"ok": True, "count": len(load_registry())}
    except Exception as e:
        templates = {"ok": False, "error": str(e)}
    checks = {
        "api": {"ok": True},
        "libreoffice": {"ok": shutil.which("soffice") is not None},
        "templates": templates,
        "llm": _llm_status(),
    }
    return {"ok": all(c["ok"] for c in checks.values()), "checks": checks}


@app.get("/templates")
def templates():
    return [{"client": t.client, "brand": t.brand, "template_id": t.template_id,
             "version": t.version} for t in load_registry()]
