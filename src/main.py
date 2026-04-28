"""Main FastAPI application for FundLens data ingestion."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config import Config
from src.database.base import Base
from src.database.db import engine
from src.api import upload

# Configure logging
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app startup and shutdown events.

    Startup:
    - Initialize database tables
    - Ensure staging directory exists
    - Load schema configuration

    Shutdown:
    - Clean up resources
    """
    # Startup
    logger.info("Application starting up...")
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized")

        # Ensure staging directory exists
        Config.ensure_staging_dir()

        # Load schema configuration
        schema_config = Config.load_schema_config()
        logger.info(f"Schema loaded with {len(schema_config)} top-level keys")

        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Error during application startup: {str(e)}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Application shutting down...")
    # Add any cleanup logic here if needed
    logger.info("Application shutdown completed")


# Create FastAPI app with lifespan
app = FastAPI(
    title="FundLens Data Ingestion API",
    description="API for uploading and processing fund data",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "FundLens Data Ingestion API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=Config.LOG_LEVEL.lower(),
    )
