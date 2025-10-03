from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router as orders_router

app = FastAPI(
    title="Logistics POC API",
    description="A logistics proof-of-concept API with warehouse and order management",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"], 
    allow_credentials=True
)

# Include the orders router
app.include_router(orders_router)

@app.get('/health')
def health():
    """Health check endpoint"""
    return {"ok": True}

@app.get('/warehouses')
def warehouses():
    """Get list of available warehouses"""
    return [
        {"id":"W-BRAMPTON-DC","name":"Martin Brower Brampton DC","lat":43.7505,"lon":-79.6773},
        {"id":"W-OSHAWA-DC","name":"Martin Brower Oshawa DC","lat":43.9537,"lon":-78.8690}
    ]