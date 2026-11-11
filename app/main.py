"""
CashMind AI Application Entrypoint
Initializes FastAPI, request tracing, global error handling, and API routes.
"""

import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.exceptions import CashMindError
from app.core.logging import logger, request_id_ctx
from app.core.providers.groq_provider import get_groq_provider
from app.core.responses import ErrorDetail, ErrorResponse
from app.modules.generate.router import router as generate_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context initializing provider connections and resources."""
    logger.info(f"Starting {settings.SERVICE_NAME} AI service on port {settings.PORT}...")
    provider = get_groq_provider()
    logger.info(f"Groq provider initialized. Key pool metrics: {provider.key_pool.get_status()}")
    yield
    logger.info(f"Shutting down {settings.SERVICE_NAME} AI service.")


app = FastAPI(
    title="CashMind AI Service",
    description="CashMind AI Reasoning and Content Generation Microservice",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    """Assigns unique correlation ID to each request and binds it to logging context."""
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_ctx.set(req_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
    finally:
        request_id_ctx.reset(token)


# Centralized Exception Handlers
@app.exception_handler(CashMindError)
async def cashmind_error_handler(request: Request, exc: CashMindError) -> JSONResponse:
    """Handles domain-specific CashMind errors with consistent envelope."""
    payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code=exc.error_code,
            message=exc.message,
            details=exc.details,
        ),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=payload.model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles Pydantic request validation failures."""
    from fastapi.encoders import jsonable_encoder

    details = jsonable_encoder(exc.errors())
    first_msg = details[0]["msg"] if details else "Invalid request payload."
    payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message=first_msg,
            details=details,
        ),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=payload.model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches unexpected server errors."""
    logger.exception(f"Unhandled server error: {str(exc)}")
    payload = ErrorResponse(
        success=False,
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred.",
        ),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload.model_dump(),
    )


# Mount routers
app.include_router(generate_router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["System"])
async def root_health():
    """Root health probe."""
    return {"status": "ok", "service": settings.SERVICE_NAME}
