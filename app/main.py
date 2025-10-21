# app/main.py - FIXED VERSION
from app.core.redis_config import redis_manager
from app.security import AuditMiddleware
from app.security import RateLimitMiddleware
from app.api.notifications import router as notification_router
from app.api.officer_dashboard import router as dashboard_router
from app.api.appointments import router as appointment_router
from app.api import diagnostics, metrics, health
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sys
import os
from app.api import auth, passport_applications, users  # Add users

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings
from app.database import SessionLocal  # ← ADD THIS IMPORT!
from app.api.auth import router as auth_router
from app.api.passport_applications import router as passport_router

# Create FastAPI instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc UI
)

# Path to your React build
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

# Serve static assets (like JS/CSS/images)
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

# Serve the React index.html for the root route
@app.get("/")
async def serve_react_app():
    index_path = os.path.join(frontend_path, "index.html")
    return FileResponse(index_path)

# ← FIX: Add the db_session_factory parameter!
app.add_middleware(
    AuditMiddleware,
    db_session_factory=SessionLocal  # ← THIS WAS MISSING!
)

app.add_middleware(
    RateLimitMiddleware, 
    redis_url=settings.REDIS_URL
)

# Configure CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "https://lesotho-passport-system-production.up.railway.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include authentication routes
app.include_router(
    auth_router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication"]
)

# Include passport application routes
app.include_router(
    passport_router,
    prefix=f"{settings.API_V1_STR}/passport-applications",
    tags=["Passport Applications"]
)

app.include_router(
    notification_router,
    prefix=f"{settings.API_V1_STR}/notifications",
    tags=["SMS Notifications"]
)

app.include_router(
    dashboard_router,
    prefix=f"{settings.API_V1_STR}/officer",
    tags=["Officer Dashboard"]
)

app.include_router(
    appointment_router,
    prefix=f"{settings.API_V1_STR}/appointments",
    tags=["Appointment Scheduling"]
)

app.include_router(
    users.router, prefix="/api/v1/users", 
    tags=["User Management"]
)

app.include_router(
    diagnostics.router, 
    prefix="/api/v1", 
    tags=["Diagnostics"]
)

app.include_router(
    health.router, 
    prefix="/api/v1", 
    tags=["Health"]
)

app.include_router(
    metrics.router, 
    prefix="/api/v1", 
    tags=["Metrics"]
)

# Add this startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        redis_manager.initialize()
        print("✅ Redis initialized successfully")
    except Exception as e:
        print(f"❌ Redis initialization failed: {e}")

# Health check endpoints
@app.get("/")
async def root():
    """
    Root endpoint - Health check
    """
    return {
        "message": f"{settings.PROJECT_NAME} API",
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"detail": "Frontend not found"}    

# Run the app (only when running this file directly)
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )