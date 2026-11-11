from contextlib import asynccontextmanager
import logging
import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1 import admin, analytics, assessments, assistant, auth, courses, ml, reports, students
from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.db.base import Base
from app.db.seed import seed_database
from app.db.session import SessionLocal, engine
from app.ml.model_registry import get_loaded_models

logger = configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Starting %s v%s (%s)", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
        get_loaded_models(db)
    finally:
        db.close()
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title="Gayatri AI — Enterprise Educational Intelligence Platform",
    version=settings.APP_VERSION,
    description=(
        "Enterprise educational analytics, predictive learner modeling, adaptive recommendations, "
        "assessment psychometrics, and curriculum-grounded academic intelligence API."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
    logger.info("%s %s -> %d (%.1f ms)", request.method, request.url.path, response.status_code, elapsed_ms)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error processing %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal platform error occurred. Please check server logs."},
    )


@app.get("/health", tags=["System"])
def health_check():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    finally:
        db.close()
    return {
        "status": "healthy" if db_ok else "degraded",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database_connected": db_ok,
    }


prefix = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=prefix)
app.include_router(students.router, prefix=prefix)
app.include_router(courses.router, prefix=prefix)
app.include_router(assessments.router, prefix=prefix)
app.include_router(analytics.router, prefix=prefix)
app.include_router(assistant.router, prefix=prefix)
app.include_router(admin.router, prefix=prefix)
app.include_router(ml.router, prefix=prefix)
app.include_router(reports.router, prefix=prefix)
