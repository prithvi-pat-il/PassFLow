#!/usr/bin/env python3
"""
Data import script for PassFlow
Reads routes and pricing data from Excel file and imports into database
"""

import pandas as pd
import re
from app_complete import app, db, Route, Pricing

# Excel file location
EXCEL_FILE_PATH = 'routes and price data.xlsx'

def clean_and_import_data():
    """Read Excel file and import routes and pricing data"""
    print("Starting data import from Excel file...")
    
    try:
        # Read the Excel file
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name='Monthly Price')
        print(f"✓ Excel file loaded with {len(df)} rows")
        
        with app.app_context():
            # Clear existing data (optional - comment out to keep existing data)
            print("Clearing existing route and pricing data...")
            Route.query.delete()
            Pricing.query.delete()
            db.session.commit()
            
            routes_imported = 0
            pricing_imported = 0
            current_route = None
            route_stops = []
            
            for index, row in df.iterrows():
                # Skip header row
                if index == 0:
                    continue
                
                # Check if this is a route header (contains "Route No." in column 1)
                route_header = str(row.iloc[1])
                if 'Route No.' in route_header:
                    # If we have a previous route with stops, save it
                    if current_route and route_stops:
                        save_route_with_stops(current_route, route_stops)
                        routes_imported += 1
                        route_stops = []
                    
                    # Extract route information
                    route_parts = route_header.split('Route No.')
                    if len(route_parts) > 1:
                        route_name = route_parts[0].strip()
                        route_number = route_parts[1].strip()
                        
                        # Create new route
                        current_route = {
                            'name': f"{route_name} - Route {route_number}",
                            'bus_number': f"BUS{route_number.zfill(2)}",
                            'route_id': route_number
                        }
                        print(f"Found route: {current_route['name']}")
                    continue
                
                # Check if this is a stop/station entry (has serial number and station name)
                try:
                    sr_no = row.iloc[1]  # Serial number in column 1
                    station_name = row.iloc[2]  # Station name in column 2
                    
                    # Skip if data is not valid
                    if pd.isna(sr_no) or pd.isna(station_name):
                        continue
                    
                    sr_no = int(sr_no)
                    station_name = str(station_name).strip()
                    
                    # Skip if station is SIT COE (destination)
                    if 'SIT COE' in station_name or 'SITCOE' in station_name:
                        continue
                    
                    # Get pricing information from column 4 (Bus Charges Per Month)
                    price_per_month = row.iloc[4]
                    
                    if not pd.isna(price_per_month) and price_per_month > 0:
                        price_per_month = float(price_per_month)
                        
                        # Add to pricing table
                        existing_pricing = Pricing.query.filter_by(location=station_name).first()
                        if not existing_pricing:
                            pricing = Pricing(location=station_name, price=price_per_month)
                            db.session.add(pricing)
                            pricing_imported += 1
                            print(f"   Added pricing: {station_name} - ₹{price_per_month}")
                        
                        # Add to current route stops
                        if current_route:
                            lat, lng = generate_coordinates(station_name, sr_no)
                            route_stops.append({
                                'name': station_name,
                                'lat': lat,
                                'lng': lng,
                                'order': sr_no
                            })
                    
                except (ValueError, TypeError, IndexError):
                    continue
            
            # Save the last route if exists
            if current_route and route_stops:
                save_route_with_stops(current_route, route_stops)
                routes_imported += 1
            
            db.session.commit()
            
            print(f"\n✅ Data import completed!")
            print(f"   Routes imported: {routes_imported}")
            print(f"   Pricing locations imported: {pricing_imported}")
            
    except FileNotFoundError:
        print(f"❌ Excel file '{EXCEL_FILE_PATH}' not found!")
    except Exception as e:
        print(f"❌ Error importing data: {str(e)}")

def generate_coordinates(station_name, order):
    """Generate approximate coordinates for stations (placeholder implementation)"""
    # Base coordinates around Kolhapur area (adjust as needed)
    base_lat = 16.7050
    base_lng = 74.2433
    
    # Generate coordinates in a rough circle around base point
    import math
    angle = (order * 30) % 360  # Distribute stops in a circle
    radius = 0.01 + (order * 0.005)  # Varying distance from center
    
    lat = base_lat + (radius * math.cos(math.radians(angle)))
    lng = base_lng + (radius * math.sin(math.radians(angle)))
    
    return round(lat, 6), round(lng, 6)

def save_route_with_stops(route_info, stops):
    """Save route with its stops to database"""
    if not stops:
        return
    
    # Sort stops by order
    stops.sort(key=lambda x: x['order'])
    
    # Create route
    route = Route(
        name=route_info['name'],
        bus_number=route_info['bus_number']
    )
    
    # Set stops (remove order field for JSON storage)
    stops_for_json = [{'name': stop['name'], 'lat': stop['lat'], 'lng': stop['lng']} for stop in stops]
    route.set_stops(stops_for_json)
    
    # Set basic timings
    route.set_timings({
        'First Bus': '06:00 AM',
        'Last Bus': '09:00 PM',
        'Frequency': 'Every 45-60 minutes'
    })
    
    db.session.add(route)
    print(f"   Added route: {route.name} with {len(stops)} stops")

if __name__ == '__main__':
    clean_and_import_data()
