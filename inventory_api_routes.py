"""
Enhanced inventory API routes with McDonald's specific data
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
import psycopg2
from pydantic import BaseModel
import json
import random
from fastapi import Body
import psycopg2

router = APIRouter(prefix="/inventory", tags=["inventory"])

class InventoryItem(BaseModel):
    item_id: str
    name: str
    category: str
    unit: str
    shelf_life_days: Optional[int]

class StockRecord(BaseModel):
    location_type: str
    location_id: str
    item_id: str
    item_name: str
    category: str
    quantity: float
    reserved_quantity: float
    unit: str

class VehicleFleet(BaseModel):
    truck_id: str
    type: str
    capacity_kg: int
    capacity_m3: int
    fuel_efficiency: float
    status: str
    last_maintenance: Optional[str]

class InventorySummary(BaseModel):
    total_items: int
    total_stock_records: int
    categories: Dict[str, int]
    location_types: Dict[str, Dict[str, Any]]
    fleet_summary: Dict[str, Dict[str, Any]]

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host="localhost",
        database="logistics",
        user="postgres",
        password="postgres",
        port="5432"
    )

@router.get("/items", response_model=List[InventoryItem])
async def get_inventory_items(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in item names"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of items to return")
):
    """Get all inventory items with optional filtering"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT item_id, name, category, unit, shelf_life_days
            FROM inventory_items
            WHERE 1=1
        """
        params = []
        
        if category:
            query += " AND category = %s"
            params.append(category)
        
        if search:
            query += " AND name ILIKE %s"
            params.append(f"%{search}%")
        
        query += " ORDER BY category, name LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        items = []
        for row in results:
            items.append(InventoryItem(
                item_id=row[0],
                name=row[1],
                category=row[2],
                unit=row[3],
                shelf_life_days=row[4]
            ))
        
        cursor.close()
        conn.close()
        
        return items
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/stock", response_model=List[StockRecord])
async def get_stock_levels(
    location_type: Optional[str] = Query(None, description="Filter by location type"),
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    category: Optional[str] = Query(None, description="Filter by item category"),
    low_stock: Optional[bool] = Query(None, description="Show only low stock items"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """Get current stock levels with optional filtering"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT s.location_type, s.location_id, s.item_id, i.name, i.category, 
                   s.quantity, s.reserved_quantity, i.unit
            FROM inventory_stock s
            JOIN inventory_items i ON s.item_id = i.item_id
            WHERE 1=1
        """
        params = []
        
        if location_type:
            query += " AND s.location_type = %s"
            params.append(location_type)
        
        if location_id:
            query += " AND s.location_id = %s"
            params.append(location_id)
        
        if category:
            query += " AND i.category = %s"
            params.append(category)
        
        if low_stock:
            query += " AND s.quantity < 50"  # Define low stock threshold
        
        query += " ORDER BY s.location_type, s.location_id, i.category, i.name LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        stocks = []
        for row in results:
            stocks.append(StockRecord(
                location_type=row[0],
                location_id=row[1],
                item_id=row[2],
                item_name=row[3],
                category=row[4],
                quantity=float(row[5]),
                reserved_quantity=float(row[6]),
                unit=row[7]
            ))
        
        cursor.close()
        conn.close()
        
        return stocks
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/fleet", response_model=List[VehicleFleet])
async def get_vehicle_fleet(
    truck_type: Optional[str] = Query(None, description="Filter by truck type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of vehicles to return")
):
    """Get vehicle fleet information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT truck_id, type, capacity_kg, capacity_m3, fuel_efficiency, 
                   status, last_maintenance
            FROM vehicle_fleet
            WHERE 1=1
        """
        params = []
        
        if truck_type:
            query += " AND type = %s"
            params.append(truck_type)
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        query += " ORDER BY truck_id LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        fleet = []
        for row in results:
            fleet.append(VehicleFleet(
                truck_id=row[0],
                type=row[1],
                capacity_kg=row[2],
                capacity_m3=row[3],
                fuel_efficiency=float(row[4]),
                status=row[5],
                last_maintenance=str(row[6]) if row[6] else None
            ))
        
        cursor.close()
        conn.close()
        
        return fleet
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/summary", response_model=InventorySummary)
async def get_inventory_summary():
    """Get comprehensive inventory and fleet summary"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total items count
        cursor.execute("SELECT COUNT(*) FROM inventory_items")
        result = cursor.fetchone()
        total_items = result[0] if result else 0
        
        # Get total stock records count
        cursor.execute("SELECT COUNT(*) FROM inventory_stock")
        result = cursor.fetchone()
        total_stock_records = result[0] if result else 0
        
        # Get items by category
        cursor.execute("""
            SELECT category, COUNT(*) as item_count
            FROM inventory_items
            GROUP BY category
            ORDER BY item_count DESC
        """)
        categories = {}
        for category, count in cursor.fetchall():
            categories[category] = count
        
        # Get stock by location type
        cursor.execute("""
            SELECT location_type, 
                   COUNT(*) as record_count,
                   SUM(quantity) as total_quantity
            FROM inventory_stock
            GROUP BY location_type
            ORDER BY total_quantity DESC
        """)
        location_types = {}
        for location_type, record_count, total_quantity in cursor.fetchall():
            location_types[location_type] = {
                "record_count": record_count,
                "total_quantity": float(total_quantity) if total_quantity else 0
            }
        
        # Get fleet summary
        cursor.execute("""
            SELECT type, 
                   COUNT(*) as truck_count,
                   SUM(capacity_kg) as total_capacity_kg,
                   AVG(fuel_efficiency) as avg_efficiency
            FROM vehicle_fleet
            GROUP BY type
            ORDER BY truck_count DESC
        """)
        fleet_summary = {}
        for truck_type, truck_count, total_capacity, avg_efficiency in cursor.fetchall():
            fleet_summary[truck_type] = {
                "truck_count": truck_count,
                "total_capacity_kg": total_capacity if total_capacity else 0,
                "avg_fuel_efficiency": float(avg_efficiency) if avg_efficiency else 0
            }
        
        cursor.close()
        conn.close()
        
        return InventorySummary(
            total_items=total_items,
            total_stock_records=total_stock_records,
            categories=categories,
            location_types=location_types,
            fleet_summary=fleet_summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/categories")
async def get_categories():
    """Get all unique item categories"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT category FROM inventory_items ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return {"categories": categories}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/locations")
async def get_locations():
    """Get all unique location IDs by type"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT location_type, location_id 
            FROM inventory_stock 
            GROUP BY location_type, location_id 
            ORDER BY location_type, location_id
        """)
        
        locations = {}
        for location_type, location_id in cursor.fetchall():
            if location_type not in locations:
                locations[location_type] = []
            locations[location_type].append(location_id)
        
        cursor.close()
        conn.close()
        
        return {"locations": locations}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")



# Admin helpers (development only)
@router.post("/admin/clear")
async def admin_clear_inventory(clear_items: bool = Body(False, description="Also clear inventory_items table")):
    """Clear inventory_stock and optionally inventory_items. Development use only."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM inventory_stock")
        if clear_items:
            cur.execute("DELETE FROM inventory_items")
        conn.commit()
        cur.close()
        conn.close()
        return {"cleared_stock": True, "cleared_items": bool(clear_items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/admin/seed_random")
async def admin_seed_random(count: int = Body(100, description="Number of random stock records to upsert")):
    """Seed random stock records for testing. Will use existing inventory_items where possible."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Fetch available items
        cur.execute("SELECT item_id FROM inventory_items")
        items = [r[0] for r in cur.fetchall()]
        if not items:
            # If no items present, create a few placeholder items
            sample = ["ITEM_A", "ITEM_B", "ITEM_C", "ITEM_D"]
            for it in sample:
                cur.execute("INSERT INTO inventory_items (item_id, name, category, unit) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING", (it, it, 'unknown', 'each'))
            conn.commit()
            items = sample

        locations = ["FRAN_001","FRAN_002","FRAN_003","FRAN_004","FRAN_005","WH_NORTH_GTA","WH_SOUTH_GTA","WH_CENTRAL_GTA"]

        upsert = """
            INSERT INTO inventory_stock (location_type, location_id, item_id, quantity)
            VALUES (%s,%s,%s,%s)
            ON CONFLICT (location_type, location_id, item_id)
            DO UPDATE SET quantity = EXCLUDED.quantity, last_updated = CURRENT_TIMESTAMP
        """

        for _ in range(count):
            item = random.choice(items)
            loc = random.choice(locations)
            loc_type = 'franchisee' if loc.startswith('FRAN') else ('warehouse' if loc.startswith('WH') else 'distribution')
            qty = round(random.uniform(5, 200), 2)
            cur.execute(upsert, (loc_type, loc, item, qty))

        conn.commit()
        cur.close()
        conn.close()
        return {"seeded": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post('/admin/seed_full')
async def admin_seed_full():
    """Run the full McDonald's seeder script to populate items, stock and fleet. Development only."""
    try:
        # Import and run seeder main
        from seed_mcdonalds_inventory import main as seed_main
        seed_main()
        return {"seed_full": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeder error: {str(e)}")

@router.get("/dashboard-data")
async def get_dashboard_data():
    """Get all data needed for dashboard widgets"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get low stock alerts (items with quantity < 50)
        cursor.execute("""
            SELECT i.name, i.category, s.location_type, s.location_id, s.quantity, i.unit
            FROM inventory_stock s
            JOIN inventory_items i ON s.item_id = i.item_id
            WHERE s.quantity < 50
            ORDER BY s.quantity ASC
            LIMIT 20
        """)
        
        low_stock_alerts = []
        for row in cursor.fetchall():
            low_stock_alerts.append({
                "item_name": row[0],
                "category": row[1],
                "location_type": row[2],
                "location_id": row[3],
                "quantity": float(row[4]),
                "unit": row[5]
            })
        
        # Get fleet status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM vehicle_fleet
            GROUP BY status
        """)
        
        fleet_status = {}
        for status, count in cursor.fetchall():
            fleet_status[status] = count
        
        # Get top categories by stock value (simplified)
        cursor.execute("""
            SELECT i.category, COUNT(*) as item_count, SUM(s.quantity) as total_quantity
            FROM inventory_items i
            JOIN inventory_stock s ON i.item_id = s.item_id
            GROUP BY i.category
            ORDER BY total_quantity DESC
            LIMIT 10
        """)
        
        category_stats = []
        for category, item_count, total_quantity in cursor.fetchall():
            category_stats.append({
                "category": category,
                "item_count": item_count,
                "total_quantity": float(total_quantity) if total_quantity else 0
            })
        
        cursor.close()
        conn.close()
        
        return {
            "low_stock_alerts": low_stock_alerts,
            "fleet_status": fleet_status,
            "category_stats": category_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")