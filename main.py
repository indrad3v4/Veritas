"""
Veritas - AI-Powered Communication WebApp for UKNF
FastAPI Application Entry Point
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.Externals.api.middleware import setup_middleware
from src.Externals.api.routes import auth, reports, users, entities, health
from src.Externals.websocket.handlers import router as websocket_router
from src.Externals.database.connection import initialize_database

# Create FastAPI app
app = FastAPI(
    title="Veritas Backend API",
    description="AI-powered communication platform for UKNF",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup middleware
setup_middleware(app)

# Include API routes
app.include_router(auth.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(entities.router, prefix="/api")
app.include_router(health.router, prefix="/api")

# Include WebSocket
app.include_router(websocket_router)

@app.on_event("startup")
async def startup_event():
    """Initialize database and demo data"""
    await initialize_database()
    print("✅ Veritas Backend API started successfully!")
    print("📡 REST API: http://0.0.0.0:8000/docs")
    print("🔌 WebSocket: ws://0.0.0.0:8000/ws")

@app.get("/")
async def root():
    return {
        "message": "Veritas Backend API - AI-Powered UKNF Communication",
        "docs": "/docs",
        "health": "/api/health",
        "websocket": "/ws?user_id={user_id}",
        "version": "1.0.0",
        "team": "Console.log(Win)"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
