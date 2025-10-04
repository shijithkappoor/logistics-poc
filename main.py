"""
Main FastAPI application for logistics routing system
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routing_routes import router as routing_router
from inventory_routes import router as inventory_router
from warehouse_routes import router as warehouse_router
from delivery_locations_routes import router as delivery_locations_router
from inventory_api_routes import router as inventory_api_router
import threading
import time
import random
import uuid
from datetime import datetime

# Import the in-process inventory simulator to post events directly
from inventory_routes import simulator as inventory_simulator
from inventory_models import StockEvent
# Import orders router from the backend package so the root app exposes /orders
from backend.app.routes import router as orders_router

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
app.include_router(warehouse_router)
app.include_router(delivery_locations_router)
app.include_router(inventory_api_router)
# Expose orders endpoints from the backend package at /orders
app.include_router(orders_router)


def _background_inventory_feeder(stop_event: threading.Event, interval: int = 60):
    """Background job that periodically generates stock events (consume/replenish)."""
    franchisees = ['FRAN_001', 'FRAN_002', 'FRAN_003', 'FRAN_004', 'FRAN_005']
    sample_items = [
        "BREAD_WHITE", "MILK_2PCT", "EGGS_DOZEN", "BUTTER_SALTED", "CHEESE_CHEDDAR",
        "YOGURT_VANILLA", "APPLES_GALA", "BANANAS"
    ]

    while not stop_event.is_set():
        try:
            # Generate a small batch of consume events
            events = []
            num_events = random.randint(1, 3)
            for _ in range(num_events):
                item = random.choice(sample_items)
                fran = random.choice(franchisees)
                evt = {
                    'id': str(uuid.uuid4()),
                    'type': 'consume',
                    'ts': datetime.utcnow(),
                    'franchisee_id': fran,
                    'item_id': item,
                    'qty': round(random.uniform(0.5, 5.0), 2)
                }
                events.append(evt)

            # Use the simulator's process_events (expects list of StockEvent Pydantic models)
            # inventory_simulator.process_events will validate and apply them
            # Convert plain dict events to StockEvent models (the simulator expects Pydantic models)
            model_events = []
            for e in events:
                if isinstance(e, dict):
                    try:
                        # Construct a StockEvent pydantic model from the dict
                        model_events.append(StockEvent(**e))
                    except Exception as conv_err:
                        # If conversion fails, log and skip the problematic event
                        print(f"Background feeder: failed to convert event to StockEvent: {conv_err} - event={e}")
                else:
                    model_events.append(e)

            inventory_simulator.process_events(model_events)
        except Exception as e:
            print(f"Background feeder error: {e}")

        # sleep for the configured interval
        stop_event.wait(interval)


@app.on_event('startup')
def _start_background_feeder():
    stop_event = threading.Event()
    feeder_thread = threading.Thread(target=_background_inventory_feeder, args=(stop_event, 60), daemon=True)
    feeder_thread.start()
    app.state._inventory_feeder = (feeder_thread, stop_event)


@app.on_event('shutdown')
def _stop_background_feeder():
    v = getattr(app.state, '_inventory_feeder', None)
    if v:
        thread, stop_event = v
        stop_event.set()
        thread.join(timeout=2)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Logistics Management API",
        "version": "1.0.0",
        "services": ["routing", "inventory", "warehouses", "delivery-locations", "inventory-api"],
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "logistics-management-api",
        "services": ["routing", "inventory", "warehouses"]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )