"""
LexOrch-KG — FastAPI Application Entry Point
Wires together all routers, middleware, startup/shutdown lifecycle, and health check.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from loguru import logger

from app.api.v1 import auth, cases, reports, admin
from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import configure_logging
from app.infrastructure.neo4j.client import neo4j_client
from app.infrastructure.chromadb.client import chromadb_client


# =============================================================================
# Lifespan — Startup & Shutdown
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    # ── STARTUP ────────────────────────────────────────────────────────────
    configure_logging()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Create upload/reports directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.reports_dir, exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Initialize PostgreSQL schema (async engine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("PostgreSQL tables created/verified")

    # Connect to Neo4j
    try:
        await neo4j_client.connect()
        await neo4j_client.create_schema_constraints()
        logger.info("Neo4j connected and schema constraints applied")
    except Exception as e:
        logger.warning(f"Neo4j connection failed (non-fatal): {e}")

    # Connect to ChromaDB
    try:
        await chromadb_client.connect()
        logger.info("ChromaDB connected")
    except Exception as e:
        logger.warning(f"ChromaDB connection failed (non-fatal): {e}")

    # Bootstrap admin user if not exists
    await _bootstrap_admin()

    logger.success(f"{settings.app_name} startup complete")
    yield

    # ── SHUTDOWN ───────────────────────────────────────────────────────────
    await neo4j_client.close()
    await engine.dispose()
    logger.info(f"{settings.app_name} shutdown complete")


async def _bootstrap_admin() -> None:
    """Create the default admin user if no admin exists."""
    from app.core.database import AsyncSessionLocal
    from app.repositories.repositories import UserRepository
    from app.infrastructure.postgres.models import UserRole
    from app.core.security import get_password_hash

    async with AsyncSessionLocal() as db:
        repo = UserRepository(db)
        existing = await repo.get_by_email(settings.admin_email)
        if not existing:
            await repo.create(
                email=settings.admin_email,
                hashed_password=get_password_hash(settings.admin_password),
                first_name=settings.admin_first_name,
                last_name=settings.admin_last_name,
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
            )
            await db.commit()
            logger.info(f"Admin user bootstrapped: {settings.admin_email}")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title=settings.app_name,
    description=(
        "Explainable Agentic Legal Reasoning for Judicial Decision Support "
        "using Multi-Agent Orchestration and Knowledge Graphs.\n\n"
        "⚠️ **DISCLAIMER**: This system is a decision SUPPORT tool only. "
        "It does NOT replace human legal professionals. All recommendations "
        "require human expert review before any legal action."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# =============================================================================
# Middleware
# =============================================================================

# CORS — allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Trusted host middleware (production security)
if settings.is_production:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["lexorch.ai", "*.lexorch.ai"])


# =============================================================================
# Routers
# =============================================================================

API_PREFIX = settings.api_prefix  # /api/v1

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(cases.router, prefix=API_PREFIX)
app.include_router(reports.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)


# =============================================================================
# Root & Health Endpoints
# =============================================================================

@app.get("/", tags=["Root"], summary="API information")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Explainable Agentic Legal Reasoning Platform",
        "disclaimer": (
            "This system is a legal decision SUPPORT tool only. "
            "Final decisions must be made by qualified human legal professionals."
        ),
        "docs": "/docs",
        "status": "operational",
    }


@app.get("/health", tags=["Health"], summary="Health check")
async def health_check():
    """Verify all services are reachable."""
    health = {
        "status": "healthy",
        "version": settings.app_version,
        "services": {},
    }

    # Check Neo4j
    try:
        neo4j_ok = await neo4j_client.verify_connectivity()
        health["services"]["neo4j"] = "healthy" if neo4j_ok else "degraded"
    except Exception:
        health["services"]["neo4j"] = "unavailable"

    # Check ChromaDB
    try:
        chroma_ok = await chromadb_client.heartbeat()
        health["services"]["chromadb"] = "healthy" if chroma_ok else "degraded"
    except Exception:
        health["services"]["chromadb"] = "unavailable"

    health["services"]["postgres"] = "healthy"  # If we got here, postgres is up

    return health
