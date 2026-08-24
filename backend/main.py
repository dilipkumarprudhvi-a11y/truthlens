"""
TruthLens AI — Main FastAPI Application Entrypoint
Evidence-first credibility, claim verification, and linguistic analysis engine.
"""

import sys
import os
import time
import uuid
import logging
from contextlib import asynccontextmanager

# Robust path handling for both root execution and Render backend rootDir execution
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from backend.db.session import init_db
    from backend.api.routes import router as api_router
except (ImportError, ModuleNotFoundError):
    from db.session import init_db
    from api.routes import router as api_router

# Configure Structured Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] [req_id=%(name)s]: %(message)s"
)
logger = logging.getLogger("truthlens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown handler."""
    logger.info("Initializing TruthLens database tables...")
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization warning: {e}")
    yield
    logger.info("TruthLens application shutting down.")


app = FastAPI(
    title="TruthLens AI",
    description="Evidence-Grounded Misinformation & Credibility Intelligence API",
    version="3.0.0",
    lifespan=lifespan
)


# ─── SECURITY & TRACING MIDDLEWARE ─────────────────────────
class SecurityAndTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        start_time = time.time()

        # Structured request start log (never logs user body)
        logger.info(f"Incoming {request.method} {request.url.path} (id={req_id})")

        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Security Headers
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Response-Time-Ms"] = str(duration_ms)

        logger.info(f"Completed {request.method} {request.url.path} -> {response.status_code} in {duration_ms}ms")
        return response


app.add_middleware(SecurityAndTracingMiddleware)

# CORS Configuration
raw_cors = os.environ.get("CORS_ORIGINS", "*")
allowed_origins = [o.strip() for o in raw_cors.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ─── SAFE GLOBAL EXCEPTION HANDLER ────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = request.headers.get("X-Request-ID", "unknown")
    logger.error(f"Unhandled Exception on {request.url.path} [req_id={req_id}]: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error occurred.",
            "request_id": req_id,
            "message": "An unexpected error was encountered. Our engineers have been alerted."
        }
    )


# ─── INCLUDE API ROUTER ────────────────────────────────────
# Mounted at both root and /api prefix for maximum compatibility
app.include_router(api_router, prefix="/api", tags=["Analysis & Intelligence"])
app.include_router(api_router, tags=["Root API Compatibility"])


# ─── STATIC FRONTEND SERVING ──────────────────────────────
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>TruthLens API is active. Static frontend not found.</h1>")


@app.get("/style.css", include_in_schema=False)
def serve_css():
    css_path = os.path.join(static_dir, "style.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    return Response(content="", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def serve_js():
    js_path = os.path.join(static_dir, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    return Response(content="", media_type="application/javascript")


@app.get("/config.js", include_in_schema=False)
def serve_config():
    cfg_path = os.path.join(static_dir, "config.js")
    if os.path.exists(cfg_path):
        return FileResponse(cfg_path, media_type="application/javascript")
    return Response(content="", media_type="application/javascript")


@app.get("/robots.txt", include_in_schema=False)
def serve_robots():
    robots_path = os.path.join(static_dir, "robots.txt")
    if os.path.exists(robots_path):
        return FileResponse(robots_path, media_type="text/plain")
    return Response(content="User-agent: *\nAllow: /\n", media_type="text/plain")


@app.get("/sitemap.xml", include_in_schema=False)
def serve_sitemap():
    sitemap_path = os.path.join(static_dir, "sitemap.xml")
    if os.path.exists(sitemap_path):
        return FileResponse(sitemap_path, media_type="application/xml")
    return Response(content="", media_type="application/xml")


@app.get("/googleccc5aae6bf226ee5.html", include_in_schema=False)
def serve_google_verification():
    return Response(content="google-site-verification: googleccc5aae6bf226ee5.html\n", media_type="text/html")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)
