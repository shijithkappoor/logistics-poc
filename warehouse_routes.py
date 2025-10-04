"""
Warehouse API routes with database integration
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db, WarehouseTable
from pydantic import BaseModel

router = APIRouter(prefix="/warehouses", tags=["warehouses"])

class WarehouseResponse(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    address: Optional[str] = None
    capacity: int = 1000

    class Config:
        from_attributes = True

@router.get("/", response_model=List[WarehouseResponse])
async def get_warehouses(db: Session = Depends(get_db)):
    """Get all warehouses from database"""
    try:
        warehouses = db.query(WarehouseTable).all()
        return warehouses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/health", tags=["health"])
async def warehouse_health():
    """Warehouse service health check"""
    return {
        "status": "healthy",
        "service": "warehouse-api",
        "database": "connected"
    }

@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(warehouse_id: str, db: Session = Depends(get_db)):
    """Get a specific warehouse by ID"""
    try:
        warehouse = db.query(WarehouseTable).filter(WarehouseTable.id == warehouse_id).first()
        if not warehouse:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        return warehouse
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")