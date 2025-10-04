#!/usr/bin/env python3
"""
Script to create McDonald's location seed data for the GTA logistics dashboard.
Based on Yellow Pages data showing 263 McDonald's locations in Toronto area.
"""

import json
import sqlite3
from typing import List, Dict
import random

# Sample McDonald's locations from Yellow Pages Toronto search
MCDONALDS_LOCATIONS = [
    {"name": "McDonald's Gerrard East", "address": "970 Gerrard St E, Toronto, ON M4M 1Z3", "lat": 43.6561, "lon": -79.3485},
    {"name": "McDonald's Pape Avenue", "address": "1045 Pape Avenue, Toronto, ON M4K 3W3", "lat": 43.6752, "lon": -79.3453},
    {"name": "McDonald's Keele Street", "address": "630 Keele Street, Toronto, ON M6N 3E5", "lat": 43.6633, "lon": -79.4636},
    {"name": "McDonald's Yonge North", "address": "3400 Yonge St, Toronto, ON M4N 2M7", "lat": 43.7282, "lon": -79.4108},
    {"name": "McDonald's Gerrard West", "address": "1000 Gerrard Street E, Toronto, ON M4M 3G6", "lat": 43.6561, "lon": -79.3478},
    {"name": "McDonald's St Clair West", "address": "1168 St Clair Avenue West, Toronto, ON M6E 1B4", "lat": 43.6781, "lon": -79.4367},
    {"name": "McDonald's Ingram Drive", "address": "2 Ingram Drive, Toronto, ON M6M 2L6", "lat": 43.6912, "lon": -79.4912},
    {"name": "McDonald's Avenue Road", "address": "1890 Avenue Rd, North York, ON M5M 3Z8", "lat": 43.7156, "lon": -79.4103},
    {"name": "McDonald's Yonge Downtown", "address": "123 Yonge St, Toronto, ON M5C 1W4", "lat": 43.6506, "lon": -79.3799},
    {"name": "McDonald's Church Street", "address": "127 Church Street, Toronto, ON M5C 2G5", "lat": 43.6501, "lon": -79.3762},
    {"name": "McDonald's McCaul Street", "address": "109 McCaul Street, Toronto, ON M5T 3K5", "lat": 43.6558, "lon": -79.3913},
    {"name": "McDonald's Spadina", "address": "160 Spadina Avenue, Toronto, ON M5T 2C2", "lat": 43.6536, "lon": -79.3951},
    {"name": "McDonald's Yonge Midtown", "address": "675 Yonge Street, Toronto, ON M4Y 1T2", "lat": 43.6677, "lon": -79.3865},
    {"name": "McDonald's Bathurst", "address": "344 Bathurst Street, Toronto, ON M5T 2S3", "lat": 43.6558, "lon": -79.4026},
    {"name": "McDonald's Bloor East", "address": "345 Bloor Street East, Toronto, ON M4W 3J6", "lat": 43.6719, "lon": -79.3832},
    {"name": "McDonald's St Clair East", "address": "710 St. Clair W., Toronto, ON M6C 1B2", "lat": 43.6781, "lon": -79.4234},
    {"name": "McDonald's Dundas West", "address": "2365 Dundas Street West, Toronto, ON M6P 1W7", "lat": 43.6681, "lon": -79.4589},
    {"name": "McDonald's Eglinton East", "address": "20 Eglinton Ave E, Toronto, ON M4P 1A9", "lat": 43.7058, "lon": -79.3962},
    {"name": "McDonald's Jane Street", "address": "2020 Jane Street, North York, ON M9N 2V3", "lat": 43.7234, "lon": -79.5178},
    {"name": "McDonald's Bay Street", "address": "181 Bay St, Toronto, ON M5J 2S1", "lat": 43.6479, "lon": -79.3789},
    {"name": "McDonald's Wellington", "address": "100 Wellington St. West, Toronto, ON M5J 2N7", "lat": 43.6469, "lon": -79.3823},
    {"name": "McDonald's Eaton Centre", "address": "Urban Eatery, Toronto, ON M5B 2L9", "lat": 43.6544, "lon": -79.3807},
    {"name": "McDonald's Union Station", "address": "200 Front Street West, Toronto, ON M5V 3K2", "lat": 43.6458, "lon": -79.3806},
    {"name": "McDonald's Yonge College", "address": "470 Yonge Street, Toronto, ON M4Y 1X5", "lat": 43.6612, "lon": -79.3843},
    {"name": "McDonald's Yonge Wellesley", "address": "552 Yonge Street, Toronto, ON M4Y 1Y8", "lat": 43.6643, "lon": -79.3856},
    {"name": "McDonald's St Clair Yonge", "address": "11 St. Clair Ave East, Toronto, ON M4T 1L8", "lat": 43.6891, "lon": -79.3931},
    {"name": "McDonald's Dufferin Mall", "address": "900 Dufferin Street, Toronto, ON M6H 4E9", "lat": 43.6633, "lon": -79.4356},
    {"name": "McDonald's Danforth", "address": "1735 Danforth Avenue, Toronto, ON M4C 1H9", "lat": 43.6889, "lon": -79.3234},
    {"name": "McDonald's Don Mills", "address": "747 Don Mills Road, North York, ON M3C 1T2", "lat": 43.7234, "lon": -79.3412},
    {"name": "McDonald's St Clair Keele", "address": "2525 St. Clair Ave. West, Toronto, ON M6N 4Z5", "lat": 43.6781, "lon": -79.4712},
    {"name": "McDonald's Lawrence West", "address": "1305 Lawrence Avenue West, Toronto, ON M6L 1A5", "lat": 43.7234, "lon": -79.4456},
    {"name": "McDonald's York Mills", "address": "808 York Mills Rd., North York, ON M3B 1X8", "lat": 43.7578, "lon": -79.3623},
    {"name": "McDonald's Weston Road", "address": "2625F Weston Road, North York, ON M9N 3X2", "lat": 43.7234, "lon": -79.5234},
    {"name": "McDonald's Overlea", "address": "45 Overlea Blvd, Toronto, ON M4H 1C3", "lat": 43.7089, "lon": -79.3445},
    
    # Mississauga locations (part of GTA)
    {"name": "McDonald's Square One", "address": "100 City Centre Dr, Mississauga, ON L5B 2C9", "lat": 43.5930, "lon": -79.6412},
    {"name": "McDonald's Dundas Mississauga", "address": "3045 Dundas St W, Mississauga, ON L5L 3R8", "lat": 43.5661, "lon": -79.6845},
    {"name": "McDonald's Hurontario", "address": "1585 Hurontario St, Mississauga, ON L5G 3H7", "lat": 43.5789, "lon": -79.6234},
    {"name": "McDonald's Heartland", "address": "5650 Hurontario St, Mississauga, ON L5R 0C7", "lat": 43.5234, "lon": -79.6567},
    {"name": "McDonald's Erin Mills", "address": "5100 Erin Mills Pkwy, Mississauga, ON L5M 4Z5", "lat": 43.5456, "lon": -79.7234},
    {"name": "McDonald's Airport Road", "address": "6677 Airport Rd, Mississauga, ON L4V 1E4", "lat": 43.6789, "lon": -79.6123},
    
    # Brampton locations
    {"name": "McDonald's Queen Brampton", "address": "25 Queen St E, Brampton, ON L6V 1A2", "lat": 43.6831, "lon": -79.7567},
    {"name": "McDonald's Bramalea", "address": "25 Peel Centre Dr, Brampton, ON L6T 3R5", "lat": 43.7234, "lon": -79.7456},
    {"name": "McDonald's Steeles Brampton", "address": "499 Steeles Ave E, Brampton, ON L6W 4P7", "lat": 43.7456, "lon": -79.7123},
    {"name": "McDonald's Bovaird", "address": "315 Bovaird Dr E, Brampton, ON L6V 1N7", "lat": 43.7123, "lon": -79.7345},
    
    # Markham locations
    {"name": "McDonald's Highway 7", "address": "3601 Highway 7 E, Markham, ON L3R 0M3", "lat": 43.8456, "lon": -79.3234},
    {"name": "McDonald's Main Markham", "address": "9255 Markham Rd, Markham, ON L6E 1A1", "lat": 43.8234, "lon": -79.2567},
    {"name": "McDonald's Steeles Markham", "address": "8601 Warden Ave, Markham, ON L6G 1A5", "lat": 43.8567, "lon": -79.3123},
    {"name": "McDonald's 16th Avenue", "address": "5762 16th Ave, Markham, ON L3P 7Y1", "lat": 43.8789, "lon": -79.3456},
    
    # Richmond Hill locations
    {"name": "McDonald's Yonge Richmond Hill", "address": "9625 Yonge St, Richmond Hill, ON L4C 5T2", "lat": 43.8567, "lon": -79.4234},
    {"name": "McDonald's Bayview Richmond Hill", "address": "600 Hwy 7 E, Richmond Hill, ON L4B 2N7", "lat": 43.8234, "lon": -79.3789},
    
    # Oakville locations
    {"name": "McDonald's Trafalgar", "address": "2501 Third Line, Oakville, ON L6M 5A9", "lat": 43.4567, "lon": -79.7234},
    {"name": "McDonald's QEW Oakville", "address": "333 North Service Rd W, Oakville, ON L6M 2S2", "lat": 43.4234, "lon": -79.6789}
]

def generate_operating_hours():
    """Generate realistic operating hours for McDonald's locations."""
    # Most McDonald's are either 24/7 or have extended hours
    schedules = [
        "24 hours",  # 30% are 24/7
        "6:00 AM - 11:00 PM",  # Standard hours
        "6:00 AM - 12:00 AM",  # Late night
        "5:00 AM - 11:00 PM",  # Early start
        "6:00 AM - 10:00 PM"   # Limited hours (malls, etc.)
    ]
    weights = [0.3, 0.3, 0.2, 0.1, 0.1]
    return random.choices(schedules, weights=weights)[0]

def generate_additional_info():
    """Generate additional location info like services offered."""
    services = []
    
    # Common services (high probability)
    if random.random() > 0.1:  # 90% have drive-thru
        services.append("Drive-thru")
    if random.random() > 0.2:  # 80% have mobile ordering
        services.append("Mobile Order")
    if random.random() > 0.3:  # 70% have delivery
        services.append("McDelivery")
    if random.random() > 0.4:  # 60% have McCafé
        services.append("McCafé")
    if random.random() > 0.7:  # 30% have PlayPlace
        services.append("PlayPlace")
    if random.random() > 0.8:  # 20% are 24/7
        services.append("24/7")
    
    return ", ".join(services) if services else "Standard Service"

def create_delivery_locations_table():
    """Create the delivery_locations table in our database."""
    try:
        # Connect to the PostgreSQL database
        import psycopg2
        
        # Database connection parameters
        conn = psycopg2.connect(
            host="localhost",
            database="logistics",
            user="postgres",
            password="postgres",
            port="5432"
        )
        
        cursor = conn.cursor()
        
        # Create delivery_locations table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS delivery_locations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            address TEXT NOT NULL,
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            operating_hours VARCHAR(100),
            services TEXT,
            location_type VARCHAR(50) DEFAULT 'restaurant',
            phone VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(create_table_query)
        conn.commit()
        
        print("✅ Created delivery_locations table successfully")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

def insert_mcdonalds_locations():
    """Insert McDonald's locations into the database."""
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host="localhost",
            database="logistics",
            user="postgres",
            password="postgres",
            port="5432"
        )
        
        cursor = conn.cursor()
        
        # Clear existing McDonald's data
        cursor.execute("DELETE FROM delivery_locations WHERE location_type = 'restaurant' AND name LIKE 'McDonald%'")
        
        # Insert McDonald's locations
        insert_query = """
        INSERT INTO delivery_locations (name, address, latitude, longitude, operating_hours, services, location_type, phone)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        locations_added = 0
        for location in MCDONALDS_LOCATIONS:
            phone = f"(416) {random.randint(200, 999)}-{random.randint(1000, 9999)}"
            hours = generate_operating_hours()
            services = generate_additional_info()
            
            cursor.execute(insert_query, (
                location["name"],
                location["address"],
                location["lat"],
                location["lon"],
                hours,
                services,
                "restaurant",
                phone
            ))
            locations_added += 1
        
        conn.commit()
        
        print(f"✅ Successfully inserted {locations_added} McDonald's locations")
        
        # Verify the data
        cursor.execute("SELECT COUNT(*) FROM delivery_locations WHERE location_type = 'restaurant' AND name LIKE 'McDonald%'")
        result = cursor.fetchone()
        count = result[0] if result else 0
        print(f"📊 Total McDonald's locations in database: {count}")
        
        cursor.close()
        conn.close()
        
        return locations_added
        
    except Exception as e:
        print(f"❌ Error inserting locations: {e}")
        return 0

def create_sample_json():
    """Create a sample JSON file with all the locations for reference."""
    sample_data = []
    
    for location in MCDONALDS_LOCATIONS:
        sample_data.append({
            "name": location["name"],
            "address": location["address"],
            "coordinates": {
                "lat": location["lat"],
                "lon": location["lon"]
            },
            "operating_hours": generate_operating_hours(),
            "services": generate_additional_info(),
            "phone": f"(416) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
            "location_type": "restaurant"
        })
    
    with open("/Users/shijithk/Desktop/poc/logistics/mcdonalds_gta_locations.json", "w") as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"📄 Created sample JSON file with {len(sample_data)} locations")

def main():
    """Main function to seed McDonald's location data."""
    print("🍟 McDonald's GTA Location Seeder")
    print("=" * 40)
    
    print(f"📍 Processing {len(MCDONALDS_LOCATIONS)} McDonald's locations across GTA")
    
    # Create sample JSON file
    create_sample_json()
    
    # Create database table
    if create_delivery_locations_table():
        # Insert the locations
        count = insert_mcdonalds_locations()
        
        if count > 0:
            print("\n🎉 McDonald's location seeding completed successfully!")
            print(f"📊 Added {count} delivery locations to the database")
            print("🗺️  Coverage includes: Toronto, Mississauga, Brampton, Markham, Richmond Hill, Oakville")
            print("\n💡 These locations can now be used as delivery destinations in your logistics dashboard")
        else:
            print("\n❌ Failed to seed locations")
    else:
        print("\n❌ Failed to create database table")

if __name__ == "__main__":
    main()