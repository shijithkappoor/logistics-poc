"""
Database configuration and connection management
"""
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URLs
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/logistics")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
metadata = MetaData()

# Redis setup
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis():
    """Get Redis client"""
    return redis_client

# Database tables
class WarehouseTable(Base):
    __tablename__ = "warehouses"
    
    from sqlalchemy import Column, Integer, String, Float
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    address = Column(String)
    capacity = Column(Integer, default=1000)

class RouteTable(Base):
    __tablename__ = "routes"
    
    from sqlalchemy import Column, String, Float, DateTime, JSON
    from datetime import datetime
    
    id = Column(String, primary_key=True)
    vehicle_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    eta = Column(DateTime)
    utilization = Column(Float, default=0.0)
    stops = Column(JSON)  # Store as JSON array
    overlap_areas = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class InventoryTable(Base):
    __tablename__ = "inventory"
    
    from sqlalchemy import Column, String, Integer, DateTime
    from datetime import datetime
    
    sku = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    available = Column(Integer, default=0)
    reserved = Column(Integer, default=0)
    location = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def seed_initial_data():
    """Seed database with initial data"""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_warehouses = db.query(WarehouseTable).count()
        if existing_warehouses > 0:
            print("Data already exists, skipping seed.")
            return
        
        # Seed warehouses
        warehouses = [
            WarehouseTable(
                id="warehouse-001",
                name="Toronto Central",
                lat=43.6532,
                lon=-79.3832,
                address="100 King St W, Toronto, ON"
            ),
            WarehouseTable(
                id="warehouse-002", 
                name="Toronto East",
                lat=43.6511,
                lon=-79.3470,
                address="500 Eastern Ave, Toronto, ON"
            ),
            WarehouseTable(
                id="warehouse-003",
                name="Mississauga Hub",
                lat=43.5890,
                lon=-79.6441,
                address="2000 Airport Rd, Mississauga, ON"
            )
        ]
        
        for warehouse in warehouses:
            db.add(warehouse)
        
        # Seed inventory
        inventory_items = [
            InventoryTable(sku="WIDGET-A", name="Widget A", available=100, location="warehouse-001"),
            InventoryTable(sku="WIDGET-B", name="Widget B", available=75, location="warehouse-001"),
            InventoryTable(sku="GADGET-X", name="Gadget X", available=50, location="warehouse-002"),
            InventoryTable(sku="GADGET-Y", name="Gadget Y", available=30, location="warehouse-002"),
            InventoryTable(sku="TOOL-123", name="Tool 123", available=200, location="warehouse-003"),
        ]
        
        for item in inventory_items:
            db.add(item)
        
        db.commit()
        print("Initial data seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()
    seed_initial_data()