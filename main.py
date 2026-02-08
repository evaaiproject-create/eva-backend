"""
================================================================================
EVA BACKEND - MAIN APPLICATION
================================================================================

PURPOSE:
    This is the entry point for the Eva backend server. When you run the server,
    this file is what starts everything up.

WHAT THIS FILE DOES:
    1. Creates the FastAPI application
    2. Configures security settings (CORS)
    3. Connects all the API routers (auth, users, sessions, functions, chat)
    4. Defines basic endpoints (health check, root info)
    5. Handles global errors

TO RUN THE SERVER:
    Development: python main.py
    Production:  Deployed automatically on Cloud Run

ENDPOINTS SUMMARY:
    /              - API info (root)
    /health        - Health check (Cloud Run / internal monitoring)
    /api/health    - Health check (Android app)
    /api/auth/*    - Authentication (login, register)
    /api/users/*   - User management
    /api/sessions/*- Cross-device session sync
    /api/functions/*- Function calling framework
    /api/chat/*    - Chat with EVA
    /docs          - Interactive API documentation

ROUTE ARCHITECTURE:
    All client-facing endpoints live under the /api prefix.
    This matches the Android app's EvaApiService.kt which prefixes
    every call with "api/" (e.g., "api/auth/login", "api/chat/send").

    Root-level endpoints (/, /health) remain for infrastructure tooling
    (Cloud Run health checks, load balancers, monitoring).

================================================================================
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.api import auth, users, sessions, functions
from app.api import chat


# ================================================================================
# APPLICATION LIFESPAN
# ================================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    WHAT THIS DOES:
        - Runs code when the server starts up
        - Runs code when the server shuts down

    STARTUP:
        Prints configuration information for debugging

    SHUTDOWN:
        Prints shutdown message
    """
    # ===== STARTUP =====
    print("=" * 60)
    print("🤖 EVA Backend Starting...")
    print("=" * 60)
    print(f"Environment: {settings.environment}")
    print(f"Google Cloud Project: {settings.google_cloud_project}")
    print(f"Max Users: {settings.max_users}")
    print(f"API Host: {settings.api_host}:{settings.api_port}")
    print(f"API Prefix: /api")
    print(f"Chat Endpoint: Enabled ✓")
    print("=" * 60)

    yield  # Server runs here

    # ===== SHUTDOWN =====
    print("\n🤖 EVA Backend Shutting Down...")


# ================================================================================
# FASTAPI APPLICATION
# ================================================================================

app = FastAPI(
    title="Eva Backend API",
    description=(
        "Backend API for EVA - A personal assistant inspired by JARVIS and Baymax. "
        "Provides authentication, data persistence, cross-device sync, chat with AI, "
        "and function calling capabilities."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ================================================================================
# MIDDLEWARE
# ================================================================================

# Configure CORS (Cross-Origin Resource Sharing)
# This allows your Android app to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# ================================================================================
# API ROUTERS — all mounted under /api to match the Android app
# ================================================================================
# The Android app's EvaApiService.kt defines endpoints like:
#     @POST("api/auth/login")
#     @POST("api/chat/send")
#     @GET("api/users/me")
#
# Each router already has its own prefix (e.g., "/auth", "/chat").
# Adding prefix="/api" here gives us the full path: /api/auth/login, etc.
# This keeps every individual router file untouched.
# ================================================================================

API_PREFIX = "/api"

app.include_router(auth.router, prefix=API_PREFIX)       # /api/auth/*
app.include_router(users.router, prefix=API_PREFIX)      # /api/users/*
app.include_router(sessions.router, prefix=API_PREFIX)   # /api/sessions/*
app.include_router(functions.router, prefix=API_PREFIX)  # /api/functions/*
app.include_router(chat.router, prefix=API_PREFIX)       # /api/chat/*


# ================================================================================
# ROOT ENDPOINTS (no /api prefix — used by infrastructure, not the app)
# ================================================================================

@app.get("/")
async def root():
    """
    Root endpoint - API information.

    RETURNS:
        Basic information about the API

    EXAMPLE RESPONSE:
        {
            "name": "Eva Backend API",
            "version": "0.1.0",
            "status": "operational",
            "description": "Personal assistant backend...",
            "documentation": "/docs"
        }
    """
    return {
        "name": "Eva Backend API",
        "version": "0.1.0",
        "status": "operational",
        "description": "Personal assistant backend inspired by JARVIS and Baymax",
        "documentation": "/docs",
        "endpoints": {
            "api": "/api",
            "auth": "/api/auth",
            "chat": "/api/chat",
            "users": "/api/users",
            "sessions": "/api/sessions",
            "functions": "/api/functions",
            "health": "/api/health",
        },
        "features": [
            "Google OAuth Authentication",
            "Chat with Gemini AI",
            "Cross-device Session Sync",
            "Function Calling Framework",
        ],
    }


@app.get("/health")
async def health_check():
    """
    Root-level health check — used by Cloud Run, load balancers,
    and monitoring systems that probe the bare /health path.

    PURPOSE:
        - Cloud Run startup / liveness probes
        - External uptime monitors (e.g., UptimeRobot, GCP Health Checks)

    RETURNS:
        Server health status
    """
    return {
        "status": "healthy",
        "environment": settings.environment,
        "max_users": settings.max_users,
    }


# ================================================================================
# /api HEALTH ENDPOINT — used by the Android app
# ================================================================================
# The Android app (EvaApiService.kt) calls GET "api/health".
# Because this is a standalone endpoint (not part of any router),
# we register it directly on the app with the /api prefix.
# ================================================================================

@app.get("/api/health")
async def api_health_check():
    """
    API-level health check — used by the Android app.

    The mobile client calls GET /api/health to verify the backend
    is reachable before attempting authentication.

    RETURNS:
        Server health status (same payload as /health)
    """
    return {
        "status": "healthy",
        "environment": settings.environment,
        "max_users": settings.max_users,
    }


# ================================================================================
# GLOBAL EXCEPTION HANDLER
# ================================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.

    WHAT THIS DOES:
        If any unexpected error occurs, this catches it and returns
        a friendly error message instead of crashing.

    SECURITY:
        In production, doesn't expose error details to users
        In development, includes error message for debugging
    """
    print(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if not settings.is_production else "An error occurred",
        },
    )


# ================================================================================
# LOCAL DEVELOPMENT SERVER
# ================================================================================

if __name__ == "__main__":
    import uvicorn

    # Run the application
    # This is used for local development
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=not settings.is_production,  # Auto-reload in development
    )
