"""
Main FastAPI application for logistics routing system
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routing_routes import router as routing_router
from inventory_routes import router as inventory_router

# Create FastAPI app
app = FastAPI(
    title="Logistics Management API",
    description="Comprehensive logistics system with vehicle routing optimization and inventory management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routing_router)
app.include_router(inventory_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Logistics Management API",
        "version": "1.0.0",
        "services": ["routing", "inventory"],
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "logistics-management-api",
        "services": ["routing", "inventory"]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )