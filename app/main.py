from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.chat import router as chat_router
from app.api.chat_limit import router as chat_limit_router
from app.api.exports import router as exports_router
from app.config import settings
from app.tools.registry import TOOLS

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="ERP Buddy Chatbot", version="0.1.0")

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(chat_limit_router)
app.include_router(exports_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "tools_loaded": len(TOOLS),
        "intent_router": settings.INTENT_ROUTER_ENABLED,
        "tool_grouping": settings.TOOL_GROUPING_ENABLED,
        "history_limit": settings.CHAT_HISTORY_LIMIT,
        "cache_ttl_seconds": settings.RESPONSE_CACHE_TTL_SECONDS,
    }


@app.get("/")
def widget_demo():
    return FileResponse(STATIC_DIR / "widget-demo.html")
