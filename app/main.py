from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.postgres import postgres_client
from app.api.routes import router

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    logger.info("Starting Market Research API")
    logger.info(f"Using LLM model: {settings.llm_model}")
    
    try:
        postgres_client.init_db()
        logger.info("PostgreSQL database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")
        raise
    
    yield
    
    logger.info("Shutting down AI Market Research API")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered market research API for cryptocurrency assets",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="", tags=["research"])


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "endpoints": {
            "research": "/research (POST)",
            "health": "/health (GET)",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
