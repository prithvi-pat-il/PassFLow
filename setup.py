#!/usr/bin/env python3
"""
Setup script for PassFlow
Run this script to set up the project with sample data
"""

import os
import sys
from app_complete import app, db, User, Profile, Route, Pricing, Pass, Payment, bcrypt

# Excel file location
EXCEL_FILE_PATH = 'routes and price data.xlsx'

def setup_database():
    """Initialize database and create sample data"""
print("Setting up PassFlow...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Create default admin user
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(
                name='Administrator',
                email='admin@example.com',
                phone='1234567890',
                password=admin_password,
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("✓ Default admin user created (admin@example.com / admin123)")
        
        # Add sample pricing if none exists
        if not Pricing.query.first():
            sample_pricing = [
                Pricing(location='Kothrud', price=1500.00),
                Pricing(location='Deccan', price=1200.00),
                Pricing(location='Shivajinagar', price=1800.00),
                Pricing(location='Camp', price=1400.00),
                Pricing(location='Pimpri', price=2000.00)
            ]
            for pricing in sample_pricing:
                db.session.add(pricing)
            db.session.commit()
            print("✓ Sample pricing data added")
        
        # Add sample routes if none exist
        if not Route.query.first():
            sample_routes = [
                {
                    'name': 'College to Deccan Route',
                    'bus_number': 'MH12AB1234',
                    'stops': [
                        {"name": "College Main Gate", "lat": 18.5204, "lng": 73.8567},
                        {"name": "Deccan Gymkhana", "lat": 18.5196, "lng": 73.8553},
                        {"name": "Pune Station", "lat": 18.5314, "lng": 73.8746}
                    ],
                    'timings': {
                        "First Bus": "06:00 AM",
                        "Last Bus": "10:00 PM",
                        "Frequency": "Every 30 minutes"
                    }
                },
                {
                    'name': 'College to Kothrud Route',
                    'bus_number': 'MH12CD5678',
                    'stops': [
                        {"name": "College Main Gate", "lat": 18.5204, "lng": 73.8567},
                        {"name": "Kothrud Depot", "lat": 18.5074, "lng": 73.8077},
                        {"name": "Karve Road", "lat": 18.5089, "lng": 73.8250}
                    ],
                    'timings': {
                        "First Bus": "06:30 AM",
                        "Last Bus": "09:30 PM",
                        "Frequency": "Every 45 minutes"
                    }
                }
            ]
            
            for route_data in sample_routes:
                route = Route(
                    name=route_data['name'],
                    bus_number=route_data['bus_number']
                )
                route.set_stops(route_data['stops'])
                route.set_timings(route_data['timings'])
                db.session.add(route)
            
            db.session.commit()
            print("✓ Sample route data added")
        
print("\n🚌 PassFlow setup complete!")
        print("\nTo run the application:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run the app: python app_complete.py")
        print("\nDefault login credentials:")
        print("Admin: admin@example.com / admin123")
        print("\nAccess the application at: http://127.0.0.1:5000")

if __name__ == '__main__':
    setup_database()
