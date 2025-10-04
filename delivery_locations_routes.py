"""
Delivery locations API routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import psycopg2
from pydantic import BaseModel
import json

router = APIRouter(prefix="/delivery-locations", tags=["delivery-locations"])

class DeliveryLocation(BaseModel):
    id: int
    name: str
    address: str
    latitude: Optional[float]
    longitude: Optional[float]
    operating_hours: Optional[str]
    services: Optional[str]
    location_type: str
    phone: Optional[str]

class LocationSummary(BaseModel):
    total_locations: int
    cities: dict
    services: dict

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host="localhost",
        database="logistics",
        user="postgres",
        password="postgres",
        port="5432"
    )

@router.get("/", response_model=List[DeliveryLocation])
async def get_delivery_locations(
    city: Optional[str] = Query(None, description="Filter by city"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of locations to return"),
    search: Optional[str] = Query(None, description="Search in location names")
):
    """Get all delivery locations with optional filtering"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query with filters
        query = """
            SELECT id, name, address, latitude, longitude, operating_hours, services, location_type, phone
            FROM delivery_locations
            WHERE 1=1
        """
        params = []
        
        if city:
            query += " AND address ILIKE %s"
            params.append(f"%{city}%")
        
        if search:
            query += " AND name ILIKE %s"
            params.append(f"%{search}%")
        
        query += " ORDER BY name LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        locations = []
        for row in results:
            locations.append(DeliveryLocation(
                id=row[0],
                name=row[1],
                address=row[2],
                latitude=row[3],
                longitude=row[4],
                operating_hours=row[5],
                services=row[6],
                location_type=row[7],
                phone=row[8]
            ))
        
        cursor.close()
        conn.close()
        
        return locations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/summary", response_model=LocationSummary)
async def get_locations_summary():
    """Get summary statistics of delivery locations"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM delivery_locations")
        result = cursor.fetchone()
        total = result[0] if result else 0
        
        # Get count by city
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN address LIKE '%Toronto%' THEN 'Toronto'
                    WHEN address LIKE '%Mississauga%' THEN 'Mississauga'
                    WHEN address LIKE '%Brampton%' THEN 'Brampton'
                    WHEN address LIKE '%Markham%' THEN 'Markham'
                    WHEN address LIKE '%Richmond Hill%' THEN 'Richmond Hill'
                    WHEN address LIKE '%Oakville%' THEN 'Oakville'
                    WHEN address LIKE '%North York%' THEN 'North York'
                    ELSE 'Other GTA'
                END as city,
                COUNT(*) as count
            FROM delivery_locations
            GROUP BY city
            ORDER BY count DESC
        """)
        
        cities = {}
        for city, count in cursor.fetchall():
            cities[city] = count
        
        # Get count by services (rough analysis)
        cursor.execute("""
            SELECT 
                services,
                COUNT(*) as count
            FROM delivery_locations
            WHERE services IS NOT NULL
            GROUP BY services
            ORDER BY count DESC
            LIMIT 10
        """)
        
        services = {}
        for service, count in cursor.fetchall():
            services[service] = count
        
        cursor.close()
        conn.close()
        
        return LocationSummary(
            total_locations=total,
            cities=cities,
            services=services
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/geojson")
async def get_locations_geojson(
    city: Optional[str] = Query(None, description="Filter by city")
):
    """Get delivery locations in GeoJSON format for mapping"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT name, address, latitude, longitude, operating_hours, services, phone
            FROM delivery_locations
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """
        params = []
        
        if city:
            query += " AND address ILIKE %s"
            params.append(f"%{city}%")
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        features = []
        for row in results:
            name, address, lat, lon, hours, services, phone = row
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(lon), float(lat)]
                },
                "properties": {
                    "name": name,
                    "address": address,
                    "operating_hours": hours,
                    "services": services,
                    "phone": phone,
                    "marker-color": "#ff6b35",
                    "marker-size": "medium",
                    "marker-symbol": "restaurant"
                }
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        cursor.close()
        conn.close()
        
        return geojson
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{location_id}", response_model=DeliveryLocation)
async def get_delivery_location(location_id: int):
    """Get a specific delivery location by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, address, latitude, longitude, operating_hours, services, location_type, phone
            FROM delivery_locations
            WHERE id = %s
        """, (location_id,))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Location not found")
        
        location = DeliveryLocation(
            id=result[0],
            name=result[1],
            address=result[2],
            latitude=result[3],
            longitude=result[4],
            operating_hours=result[5],
            services=result[6],
            location_type=result[7],
            phone=result[8]
        )
        
        cursor.close()
        conn.close()
        
        return location
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")