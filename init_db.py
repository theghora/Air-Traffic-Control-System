"""
Database initialization script
Run this script to create sample data for testing the ATC system
"""

from app import create_app
from models import db, Aircraft, Runway, Gate, Taxiway, Flight, AircraftSize, AircraftStatus, RunwayStatus
from datetime import datetime, timedelta

def init_database():
    app = create_app('development')

    with app.app_context():
        # Drop all tables and recreate them
        print("Creating database tables...")
        db.drop_all()
        db.create_all()

        # Create runways
        print("Adding runways...")
        runways = [
            Runway(name='RW-09L', length=3500, status=RunwayStatus.AVAILABLE),
            Runway(name='RW-09R', length=3800, status=RunwayStatus.AVAILABLE),
            Runway(name='RW-27L', length=2800, status=RunwayStatus.AVAILABLE),
            Runway(name='RW-27R', length=2000, status=RunwayStatus.AVAILABLE),
        ]
        db.session.add_all(runways)

        # Create gates
        print("Adding gates...")
        gates = [Gate(name=f'G{i}') for i in range(1, 11)]
        db.session.add_all(gates)

        # Create taxiways
        print("Adding taxiways...")
        taxiways = [Taxiway(name=f'T{chr(65+i)}') for i in range(5)]  # TA, TB, TC, TD, TE
        db.session.add_all(taxiways)

        # Create aircraft
        print("Adding aircraft...")
        aircraft_data = [
            {'id': 'AC001', 'model': 'Boeing 737', 'size': AircraftSize.MEDIUM, 'status': AircraftStatus.PARKED},
            {'id': 'AC002', 'model': 'Airbus A380', 'size': AircraftSize.HEAVY, 'status': AircraftStatus.PARKED},
            {'id': 'AC003', 'model': 'Cessna 172', 'size': AircraftSize.SMALL, 'status': AircraftStatus.PARKED},
            {'id': 'AC004', 'model': 'Boeing 777', 'size': AircraftSize.HEAVY, 'status': AircraftStatus.IN_AIR, 'altitude': 10000, 'speed': 250},
            {'id': 'AC005', 'model': 'Airbus A320', 'size': AircraftSize.MEDIUM, 'status': AircraftStatus.IN_AIR, 'altitude': 8000, 'speed': 220},
            {'id': 'AC006', 'model': 'Bombardier CRJ', 'size': AircraftSize.SMALL, 'status': AircraftStatus.TAXIING},
        ]

        aircraft_list = []
        for data in aircraft_data:
            aircraft = Aircraft(**data)
            aircraft_list.append(aircraft)

        db.session.add_all(aircraft_list)

        # Create sample flights
        print("Adding flights...")
        now = datetime.utcnow()
        flights = [
            Flight(
                flight_number='FL001',
                aircraft_id='AC001',
                scheduled_departure=now + timedelta(hours=2),
                scheduled_arrival=now + timedelta(hours=4),
                origin='JFK',
                destination='LAX',
                status='Scheduled'
            ),
            Flight(
                flight_number='FL002',
                aircraft_id='AC004',
                scheduled_departure=now - timedelta(hours=1),
                scheduled_arrival=now + timedelta(hours=1),
                origin='ORD',
                destination='JFK',
                status='In-Flight'
            ),
            Flight(
                flight_number='FL003',
                aircraft_id='AC005',
                scheduled_departure=now - timedelta(minutes=30),
                scheduled_arrival=now + timedelta(minutes=90),
                origin='LAX',
                destination='JFK',
                status='In-Flight'
            ),
        ]

        db.session.add_all(flights)

        # Commit all changes
        db.session.commit()

        print("\n✓ Database initialized successfully!")
        print(f"  - {len(runways)} runways")
        print(f"  - {len(gates)} gates")
        print(f"  - {len(taxiways)} taxiways")
        print(f"  - {len(aircraft_list)} aircraft")
        print(f"  - {len(flights)} flights")
        print("\nYou can now start the application with: python app.py")

if __name__ == '__main__':
    init_database()
