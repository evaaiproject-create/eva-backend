"""
Eva Backend - Main Application
Personal assistant inspired by JARVIS and Baymax

This FastAPI application provides:
- Google OAuth authentication
- Multi-user support (configurable limit)
- Firestore data persistence
- Cross-device session synchronization
- Dynamic function calling framework
- RESTful API for all operations
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.api import auth, users, sessions, functions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    print("=" * 60)
    print("🤖 Eva Backend Starting...")
    print("=" * 60)
    print(f"Environment: {settings.environment}")
    print(f"Google Cloud Project: {settings.google_cloud_project}")
    print(f"Max Users: {settings.max_users}")
    print(f"API Host: {settings.api_host}:{settings.api_port}")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("\n🤖 Eva Backend Shutting Down...")


# Create FastAPI application
app = FastAPI(
    title="Eva Backend API",
    description=(
        "Backend API for Eva - A personal assistant inspired by JARVIS and Baymax. "
        "Provides authentication, data persistence, cross-device sync, and function calling."
    ),
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(sessions.router)
app.include_router(functions.router)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API information.
    
    Returns:
        API name, version, and status
    """
    return {
        "name": "Eva Backend API",
        "version": "0.1.0",
        "status": "operational",
        "description": "Personal assistant backend inspired by JARVIS and Baymax",
        "documentation": "/docs"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        System health status
    """
    return {
        "status": "healthy",
        "environment": settings.environment,
        "max_users": settings.max_users
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions.
    
    Logs the error and returns a generic error response.
    """
    print(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if not settings.is_production else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=not settings.is_production
    )
