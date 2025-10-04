#!/usr/bin/env python3
"""
Script to seed McDonald's inventory data and vehicle fleet for the logistics dashboard.
Creates realistic McDonald's menu items, ingredients, and packaging supplies.
"""

import psycopg2
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# McDonald's Menu Items and Ingredients
MCDONALDS_INVENTORY = {
    # Core Food Items
    "food_items": [
        # Burgers & Sandwiches
        {"item_id": "BIG_MAC", "name": "Big Mac", "category": "burgers", "unit": "each", "shelf_life_days": 1},
        {"item_id": "QUARTER_POUNDER", "name": "Quarter Pounder with Cheese", "category": "burgers", "unit": "each", "shelf_life_days": 1},
        {"item_id": "CHEESEBURGER", "name": "Cheeseburger", "category": "burgers", "unit": "each", "shelf_life_days": 1},
        {"item_id": "HAMBURGER", "name": "Hamburger", "category": "burgers", "unit": "each", "shelf_life_days": 1},
        {"item_id": "DOUBLE_CHEESE", "name": "Double Cheeseburger", "category": "burgers", "unit": "each", "shelf_life_days": 1},
        {"item_id": "MCCHICKEN", "name": "McChicken", "category": "chicken", "unit": "each", "shelf_life_days": 1},
        {"item_id": "SPICY_MCCHICKEN", "name": "Spicy McChicken", "category": "chicken", "unit": "each", "shelf_life_days": 1},
        {"item_id": "CRISPY_CHICKEN", "name": "Crispy Chicken Sandwich", "category": "chicken", "unit": "each", "shelf_life_days": 1},
        {"item_id": "FILET_O_FISH", "name": "Filet-O-Fish", "category": "fish", "unit": "each", "shelf_life_days": 1},
        
        # Chicken McNuggets
        {"item_id": "NUGGETS_4PC", "name": "Chicken McNuggets 4pc", "category": "nuggets", "unit": "box", "shelf_life_days": 1},
        {"item_id": "NUGGETS_6PC", "name": "Chicken McNuggets 6pc", "category": "nuggets", "unit": "box", "shelf_life_days": 1},
        {"item_id": "NUGGETS_10PC", "name": "Chicken McNuggets 10pc", "category": "nuggets", "unit": "box", "shelf_life_days": 1},
        {"item_id": "NUGGETS_20PC", "name": "Chicken McNuggets 20pc", "category": "nuggets", "unit": "box", "shelf_life_days": 1},
        
        # Breakfast
        {"item_id": "EGG_MCMUFFIN", "name": "Egg McMuffin", "category": "breakfast", "unit": "each", "shelf_life_days": 1},
        {"item_id": "SAUSAGE_MCMUFFIN", "name": "Sausage McMuffin", "category": "breakfast", "unit": "each", "shelf_life_days": 1},
        {"item_id": "HOTCAKES", "name": "Hotcakes", "category": "breakfast", "unit": "serving", "shelf_life_days": 1},
        {"item_id": "HASH_BROWNS", "name": "Hash Browns", "category": "breakfast", "unit": "each", "shelf_life_days": 1},
        
        # Sides
        {"item_id": "FRIES_SMALL", "name": "World Famous Fries Small", "category": "sides", "unit": "serving", "shelf_life_days": 1},
        {"item_id": "FRIES_MEDIUM", "name": "World Famous Fries Medium", "category": "sides", "unit": "serving", "shelf_life_days": 1},
        {"item_id": "FRIES_LARGE", "name": "World Famous Fries Large", "category": "sides", "unit": "serving", "shelf_life_days": 1},
        {"item_id": "APPLE_SLICES", "name": "Apple Slices", "category": "sides", "unit": "bag", "shelf_life_days": 3},
        
        # Desserts
        {"item_id": "MCFLURRY_OREO", "name": "McFlurry with Oreo Cookies", "category": "desserts", "unit": "cup", "shelf_life_days": 1},
        {"item_id": "MCFLURRY_MMNO", "name": "McFlurry with M&M's", "category": "desserts", "unit": "cup", "shelf_life_days": 1},
        {"item_id": "APPLE_PIE", "name": "Baked Apple Pie", "category": "desserts", "unit": "each", "shelf_life_days": 2},
        {"item_id": "COOKIES", "name": "Chocolate Chip Cookies", "category": "desserts", "unit": "box", "shelf_life_days": 7},
    ],
    
    # Raw Ingredients
    "ingredients": [
        # Meat & Protein
        {"item_id": "BEEF_PATTY_REG", "name": "Regular Beef Patty", "category": "meat", "unit": "kg", "shelf_life_days": 3},
        {"item_id": "BEEF_PATTY_QTR", "name": "Quarter Pound Beef Patty", "category": "meat", "unit": "kg", "shelf_life_days": 3},
        {"item_id": "CHICKEN_BREAST", "name": "Chicken Breast", "category": "meat", "unit": "kg", "shelf_life_days": 2},
        {"item_id": "CHICKEN_NUGGET_MIX", "name": "Chicken Nugget Mix", "category": "meat", "unit": "kg", "shelf_life_days": 2},
        {"item_id": "FISH_FILLET", "name": "Fish Fillet", "category": "meat", "unit": "kg", "shelf_life_days": 2},
        {"item_id": "SAUSAGE_PATTY", "name": "Sausage Patty", "category": "meat", "unit": "kg", "shelf_life_days": 5},
        {"item_id": "EGGS_LIQUID", "name": "Liquid Eggs", "category": "dairy", "unit": "liters", "shelf_life_days": 7},
        
        # Dairy
        {"item_id": "CHEESE_SLICE", "name": "American Cheese Slices", "category": "dairy", "unit": "kg", "shelf_life_days": 14},
        {"item_id": "MILK_2PCT", "name": "2% Milk", "category": "dairy", "unit": "liters", "shelf_life_days": 7},
        {"item_id": "BUTTER", "name": "Butter", "category": "dairy", "unit": "kg", "shelf_life_days": 30},
        {"item_id": "ICE_CREAM_VANILLA", "name": "Vanilla Ice Cream Mix", "category": "dairy", "unit": "liters", "shelf_life_days": 14},
        
        # Produce
        {"item_id": "LETTUCE", "name": "Iceberg Lettuce", "category": "produce", "unit": "kg", "shelf_life_days": 5},
        {"item_id": "ONIONS", "name": "Diced Onions", "category": "produce", "unit": "kg", "shelf_life_days": 7},
        {"item_id": "PICKLES", "name": "Pickle Slices", "category": "produce", "unit": "kg", "shelf_life_days": 30},
        {"item_id": "TOMATOES", "name": "Tomato Slices", "category": "produce", "unit": "kg", "shelf_life_days": 3},
        {"item_id": "APPLES", "name": "Apple Slices", "category": "produce", "unit": "kg", "shelf_life_days": 5},
        
        # Frozen
        {"item_id": "FRIES_FROZEN", "name": "Frozen French Fries", "category": "frozen", "unit": "kg", "shelf_life_days": 365},
        {"item_id": "HASH_BROWN_FROZEN", "name": "Frozen Hash Browns", "category": "frozen", "unit": "kg", "shelf_life_days": 365},
        {"item_id": "APPLE_PIE_FROZEN", "name": "Frozen Apple Pies", "category": "frozen", "unit": "kg", "shelf_life_days": 180},
        
        # Bakery
        {"item_id": "BUN_BIG_MAC", "name": "Big Mac Buns", "category": "bakery", "unit": "pieces", "shelf_life_days": 3},
        {"item_id": "BUN_QUARTER", "name": "Quarter Pounder Buns", "category": "bakery", "unit": "pieces", "shelf_life_days": 3},
        {"item_id": "BUN_REGULAR", "name": "Regular Hamburger Buns", "category": "bakery", "unit": "pieces", "shelf_life_days": 3},
        {"item_id": "MUFFIN_ENGLISH", "name": "English Muffins", "category": "bakery", "unit": "pieces", "shelf_life_days": 5},
        
        # Condiments & Sauces
        {"item_id": "KETCHUP", "name": "Ketchup", "category": "condiments", "unit": "liters", "shelf_life_days": 90},
        {"item_id": "MUSTARD", "name": "Yellow Mustard", "category": "condiments", "unit": "liters", "shelf_life_days": 90},
        {"item_id": "MAYO", "name": "Mayonnaise", "category": "condiments", "unit": "liters", "shelf_life_days": 60},
        {"item_id": "BIG_MAC_SAUCE", "name": "Big Mac Special Sauce", "category": "condiments", "unit": "liters", "shelf_life_days": 30},
        {"item_id": "TARTAR_SAUCE", "name": "Tartar Sauce", "category": "condiments", "unit": "liters", "shelf_life_days": 30},
        
        # Beverages
        {"item_id": "COCA_COLA_SYRUP", "name": "Coca-Cola Syrup", "category": "beverages", "unit": "liters", "shelf_life_days": 120},
        {"item_id": "SPRITE_SYRUP", "name": "Sprite Syrup", "category": "beverages", "unit": "liters", "shelf_life_days": 120},
        {"item_id": "ORANGE_JUICE", "name": "Orange Juice", "category": "beverages", "unit": "liters", "shelf_life_days": 14},
        {"item_id": "COFFEE_BEANS", "name": "McCafé Coffee Beans", "category": "beverages", "unit": "kg", "shelf_life_days": 180},
    ],
    
    # Packaging & Supplies
    "packaging": [
        {"item_id": "CUP_SMALL", "name": "Small Drink Cups", "category": "packaging", "unit": "pieces", "shelf_life_days": 365},
        {"item_id": "CUP_MEDIUM", "name": "Medium Drink Cups", "category": "packaging", "unit": "pieces", "shelf_life_days": 365},
        {"item_id": "CUP_LARGE", "name": "Large Drink Cups", "category": "packaging", "unit": "pieces", "shelf_life_days": 365},
        {"item_id": "BOX_NUGGETS", "name": "Chicken McNuggets Boxes", "category": "packaging", "unit": "pieces", "shelf_life_days": 365},
        {"item_id": "BAG_FRIES", "name": "French Fries Bags", "category": "packaging", "unit": "pieces", "shelf_life_days": 365},
        {"item_id": "WRAPPER_BURGER", "name": "Burger Wrappers", "category": "packaging", "unit": "pieces", "shelf_life_days": 365},
        {"item_id": "BAG_PAPER", "name": "Paper Bags", "category": "packaging", "unit": "pieces", "shelf_life_days": 365},
        {"item_id": "NAPKINS", "name": "Napkins", "category": "packaging", "unit": "pieces", "shelf_life_days": 365},
        {"item_id": "STRAWS", "name": "Drinking Straws", "category": "packaging", "unit": "pieces", "shelf_life_days": 365},
        {"item_id": "LIDS", "name": "Drink Cup Lids", "category": "packaging", "unit": "pieces", "shelf_life_days": 365},
    ]
}

# Vehicle Fleet Configuration
VEHICLE_FLEET = [
    # Large Trucks for long-distance distribution
    {"truck_id": "TRK001", "type": "refrigerated", "capacity_kg": 15000, "capacity_m3": 45, "fuel_efficiency": 8.5, "status": "available"},
    {"truck_id": "TRK002", "type": "refrigerated", "capacity_kg": 15000, "capacity_m3": 45, "fuel_efficiency": 8.2, "status": "available"},
    {"truck_id": "TRK003", "type": "refrigerated", "capacity_kg": 15000, "capacity_m3": 45, "fuel_efficiency": 8.7, "status": "available"},
    {"truck_id": "TRK004", "type": "refrigerated", "capacity_kg": 15000, "capacity_m3": 45, "fuel_efficiency": 8.4, "status": "available"},
    {"truck_id": "TRK005", "type": "refrigerated", "capacity_kg": 15000, "capacity_m3": 45, "fuel_efficiency": 8.6, "status": "available"},
    
    # Medium Trucks for regional distribution
    {"truck_id": "TRK006", "type": "dry_goods", "capacity_kg": 8000, "capacity_m3": 30, "fuel_efficiency": 12.5, "status": "available"},
    {"truck_id": "TRK007", "type": "dry_goods", "capacity_kg": 8000, "capacity_m3": 30, "fuel_efficiency": 12.8, "status": "available"},
    {"truck_id": "TRK008", "type": "dry_goods", "capacity_kg": 8000, "capacity_m3": 30, "fuel_efficiency": 12.3, "status": "available"},
    {"truck_id": "TRK009", "type": "refrigerated", "capacity_kg": 8000, "capacity_m3": 30, "fuel_efficiency": 11.5, "status": "available"},
    {"truck_id": "TRK010", "type": "refrigerated", "capacity_kg": 8000, "capacity_m3": 30, "fuel_efficiency": 11.8, "status": "available"},
    
    # Smaller Trucks for local delivery
    {"truck_id": "TRK011", "type": "dry_goods", "capacity_kg": 3500, "capacity_m3": 18, "fuel_efficiency": 15.2, "status": "available"},
    {"truck_id": "TRK012", "type": "dry_goods", "capacity_kg": 3500, "capacity_m3": 18, "fuel_efficiency": 15.5, "status": "available"},
    {"truck_id": "TRK013", "type": "refrigerated", "capacity_kg": 3500, "capacity_m3": 18, "fuel_efficiency": 14.8, "status": "available"},
    {"truck_id": "TRK014", "type": "refrigerated", "capacity_kg": 3500, "capacity_m3": 18, "fuel_efficiency": 14.5, "status": "available"},
    {"truck_id": "TRK015", "type": "refrigerated", "capacity_kg": 3500, "capacity_m3": 18, "fuel_efficiency": 14.9, "status": "available"},
    
    # Specialized vehicles
    {"truck_id": "TRK016", "type": "frozen", "capacity_kg": 6000, "capacity_m3": 25, "fuel_efficiency": 10.2, "status": "available"},
    {"truck_id": "TRK017", "type": "frozen", "capacity_kg": 6000, "capacity_m3": 25, "fuel_efficiency": 10.5, "status": "available"},
    {"truck_id": "TRK018", "type": "multi_temp", "capacity_kg": 12000, "capacity_m3": 40, "fuel_efficiency": 9.8, "status": "available"},
    {"truck_id": "TRK019", "type": "multi_temp", "capacity_kg": 12000, "capacity_m3": 40, "fuel_efficiency": 9.5, "status": "available"},
    {"truck_id": "TRK020", "type": "multi_temp", "capacity_kg": 12000, "capacity_m3": 40, "fuel_efficiency": 9.9, "status": "available"},
]

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host="localhost",
        database="logistics",
        user="postgres",
        password="postgres",
        port="5432"
    )

def create_inventory_tables():
    """Create inventory and vehicle tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create inventory_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_items (
                item_id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(100) NOT NULL,
                unit VARCHAR(20) NOT NULL,
                shelf_life_days INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create inventory_stock table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_stock (
                id SERIAL PRIMARY KEY,
                location_type VARCHAR(20) NOT NULL,
                location_id VARCHAR(50) NOT NULL,
                item_id VARCHAR(50) NOT NULL,
                quantity DECIMAL(10, 2) NOT NULL DEFAULT 0,
                reserved_quantity DECIMAL(10, 2) NOT NULL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES inventory_items(item_id),
                UNIQUE(location_type, location_id, item_id)
            );
        """)
        
        # Create vehicle_fleet table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_fleet (
                truck_id VARCHAR(20) PRIMARY KEY,
                type VARCHAR(50) NOT NULL,
                capacity_kg INTEGER NOT NULL,
                capacity_m3 INTEGER NOT NULL,
                fuel_efficiency DECIMAL(4, 2) NOT NULL,
                status VARCHAR(20) DEFAULT 'available',
                current_location_lat DECIMAL(10, 8),
                current_location_lon DECIMAL(11, 8),
                last_maintenance DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Created inventory and vehicle tables successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def seed_inventory_items():
    """Seed inventory items"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clear existing items
        cursor.execute("DELETE FROM inventory_stock")
        cursor.execute("DELETE FROM inventory_items")
        
        # Insert all inventory items
        all_items = (MCDONALDS_INVENTORY["food_items"] + 
                    MCDONALDS_INVENTORY["ingredients"] + 
                    MCDONALDS_INVENTORY["packaging"])
        
        insert_query = """
            INSERT INTO inventory_items (item_id, name, category, unit, shelf_life_days)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        items_added = 0
        for item in all_items:
            cursor.execute(insert_query, (
                item["item_id"],
                item["name"],
                item["category"],
                item["unit"],
                item["shelf_life_days"]
            ))
            items_added += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Successfully seeded {items_added} inventory items")
        return items_added
        
    except Exception as e:
        print(f"❌ Error seeding inventory items: {e}")
        return 0

def generate_realistic_stock_levels(item: Dict) -> Dict[str, int]:
    """Generate realistic stock levels based on item type and location"""
    base_levels = {
        # Warehouses (high stock)
        "warehouse": {
            "food_items": (50, 200),    # Prepared items - moderate stock
            "ingredients": (500, 2000), # Raw ingredients - high stock
            "packaging": (5000, 20000), # Packaging - very high stock
        },
        # Distribution centers (medium stock)
        "distribution": {
            "food_items": (20, 100),
            "ingredients": (200, 800),
            "packaging": (2000, 8000),
        },
        # Restaurants (low stock, daily delivery)
        "restaurant": {
            "food_items": (5, 50),
            "ingredients": (20, 200),
            "packaging": (200, 1000),
        }
    }
    
    # Adjust for perishability
    if item["shelf_life_days"] <= 2:
        # Highly perishable - reduce stock
        for location_type in base_levels:
            for category in base_levels[location_type]:
                min_qty, max_qty = base_levels[location_type][category]
                base_levels[location_type][category] = (min_qty // 3, max_qty // 2)
    
    result = {}
    for location_type in base_levels:
        if item["category"] in base_levels[location_type]:
            min_qty, max_qty = base_levels[location_type][item["category"]]
            result[location_type] = random.randint(min_qty, max_qty)
        else:
            # Default to ingredients level
            min_qty, max_qty = base_levels[location_type]["ingredients"]
            result[location_type] = random.randint(min_qty, max_qty)
    
    return result

def seed_inventory_stock():
    """Seed realistic inventory stock levels"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get our warehouse locations
        warehouses = ["WH_NORTH_GTA", "WH_SOUTH_GTA", "WH_CENTRAL_GTA"]
        distribution_centers = ["DC_MISSISSAUGA", "DC_SCARBOROUGH"]
        restaurants = [f"REST_{i:03d}" for i in range(1, 21)]  # 20 sample restaurants
        
        all_items = (MCDONALDS_INVENTORY["food_items"] + 
                    MCDONALDS_INVENTORY["ingredients"] + 
                    MCDONALDS_INVENTORY["packaging"])
        
        insert_query = """
            INSERT INTO inventory_stock (location_type, location_id, item_id, quantity)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (location_type, location_id, item_id) 
            DO UPDATE SET quantity = EXCLUDED.quantity, last_updated = CURRENT_TIMESTAMP
        """
        
        records_added = 0
        
        for item in all_items:
            stock_levels = generate_realistic_stock_levels(item)
            
            # Warehouse stock
            for warehouse in warehouses:
                qty = stock_levels.get("warehouse", random.randint(100, 500))
                cursor.execute(insert_query, ("warehouse", warehouse, item["item_id"], qty))
                records_added += 1
            
            # Distribution center stock
            for dc in distribution_centers:
                qty = stock_levels.get("distribution", random.randint(50, 200))
                cursor.execute(insert_query, ("distribution", dc, item["item_id"], qty))
                records_added += 1
            
            # Restaurant stock (only for frequently used items)
            if item["category"] in ["food_items", "packaging"] or item["shelf_life_days"] <= 7:
                for restaurant in restaurants[:10]:  # Only first 10 restaurants for demo
                    qty = stock_levels.get("restaurant", random.randint(5, 50))
                    cursor.execute(insert_query, ("restaurant", restaurant, item["item_id"], qty))
                    records_added += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Successfully seeded {records_added} stock records")
        return records_added
        
    except Exception as e:
        print(f"❌ Error seeding inventory stock: {e}")
        return 0

def seed_vehicle_fleet():
    """Seed vehicle fleet data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clear existing fleet
        cursor.execute("DELETE FROM vehicle_fleet")
        
        insert_query = """
            INSERT INTO vehicle_fleet (truck_id, type, capacity_kg, capacity_m3, fuel_efficiency, status, last_maintenance)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        trucks_added = 0
        for truck in VEHICLE_FLEET:
            # Generate random last maintenance date (within last 3 months)
            last_maintenance = datetime.now() - timedelta(days=random.randint(1, 90))
            
            cursor.execute(insert_query, (
                truck["truck_id"],
                truck["type"],
                truck["capacity_kg"],
                truck["capacity_m3"],
                truck["fuel_efficiency"],
                truck["status"],
                last_maintenance.date()
            ))
            trucks_added += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Successfully seeded {trucks_added} vehicles in fleet")
        return trucks_added
        
    except Exception as e:
        print(f"❌ Error seeding vehicle fleet: {e}")
        return 0

def create_sample_json():
    """Create sample JSON files for reference"""
    # Create inventory items JSON
    all_items = (MCDONALDS_INVENTORY["food_items"] + 
                MCDONALDS_INVENTORY["ingredients"] + 
                MCDONALDS_INVENTORY["packaging"])
    
    with open("/Users/shijithk/Desktop/poc/logistics/mcdonalds_inventory_items.json", "w") as f:
        json.dump(all_items, f, indent=2)
    
    # Create vehicle fleet JSON
    with open("/Users/shijithk/Desktop/poc/logistics/vehicle_fleet.json", "w") as f:
        json.dump(VEHICLE_FLEET, f, indent=2)
    
    print(f"📄 Created JSON files with {len(all_items)} inventory items and {len(VEHICLE_FLEET)} vehicles")

def generate_summary_report():
    """Generate summary report of seeded data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print("📊 McDONALD'S LOGISTICS SYSTEM - INVENTORY SUMMARY")
        print("="*60)
        
        # Inventory items by category
        cursor.execute("""
            SELECT category, COUNT(*) as item_count
            FROM inventory_items
            GROUP BY category
            ORDER BY item_count DESC
        """)
        
        print("\n🍟 INVENTORY ITEMS BY CATEGORY:")
        print("-" * 40)
        total_items = 0
        for category, count in cursor.fetchall():
            print(f"{category:15} {count:3d} items")
            total_items += count
        print("-" * 40)
        print(f"{'TOTAL':15} {total_items:3d} items")
        
        # Stock levels by location type
        cursor.execute("""
            SELECT location_type, COUNT(*) as stock_records, 
                   SUM(quantity) as total_quantity
            FROM inventory_stock
            GROUP BY location_type
            ORDER BY total_quantity DESC
        """)
        
        print("\n📦 STOCK DISTRIBUTION BY LOCATION TYPE:")
        print("-" * 50)
        for location_type, records, total_qty in cursor.fetchall():
            print(f"{location_type:15} {records:4d} records  {total_qty:10,.0f} units")
        
        # Vehicle fleet summary
        cursor.execute("""
            SELECT type, COUNT(*) as truck_count,
                   SUM(capacity_kg) as total_capacity_kg,
                   AVG(fuel_efficiency) as avg_efficiency
            FROM vehicle_fleet
            GROUP BY type
            ORDER BY truck_count DESC
        """)
        
        print("\n🚛 VEHICLE FLEET BY TYPE:")
        print("-" * 60)
        for truck_type, count, capacity, efficiency in cursor.fetchall():
            print(f"{truck_type:15} {count:2d} trucks  {capacity:6,.0f}kg  {efficiency:4.1f}L/100km")
        
        # Top 10 inventory items by total stock
        cursor.execute("""
            SELECT ii.name, ii.category, SUM(is.quantity) as total_stock
            FROM inventory_items ii
            JOIN inventory_stock is ON ii.item_id = is.item_id
            GROUP BY ii.item_id, ii.name, ii.category
            ORDER BY total_stock DESC
            LIMIT 10
        """)
        
        print("\n🏆 TOP 10 ITEMS BY TOTAL STOCK:")
        print("-" * 70)
        for name, category, stock in cursor.fetchall():
            print(f"{name:35} ({category:12}) {stock:8,.0f} units")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error generating summary: {e}")

def main():
    """Main function to seed McDonald's inventory and fleet data"""
    print("🍟 McDonald's Inventory & Fleet Seeder")
    print("=" * 45)
    
    # Create sample JSON files first
    create_sample_json()
    
    # Create database tables
    if not create_inventory_tables():
        return
    
    # Seed inventory items
    items_count = seed_inventory_items()
    if items_count == 0:
        return
    
    # Seed stock levels
    stock_count = seed_inventory_stock()
    if stock_count == 0:
        return
    
    # Seed vehicle fleet
    fleet_count = seed_vehicle_fleet()
    if fleet_count == 0:
        return
    
    print("\n🎉 McDonald's Logistics Data Seeding Completed!")
    print(f"📊 {items_count} inventory items seeded")
    print(f"📦 {stock_count} stock records created")
    print(f"🚛 {fleet_count} vehicles added to fleet")
    
    # Generate summary report
    generate_summary_report()
    
    print("\n💡 Data is now ready for your logistics dashboard!")
    print("🗺️  Use the API endpoints to integrate with your frontend")

if __name__ == "__main__":
    main()