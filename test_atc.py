import pytest
from app import create_app
from models import db, Aircraft, Runway, AircraftSize, AircraftStatus, RunwayStatus
from services import ConstraintService, ConflictDetectionService, QueueService

@pytest.fixture
def app():
    """Create test application"""
    app = create_app('development')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def sample_aircraft(app):
    """Create sample aircraft"""
    with app.app_context():
        aircraft = Aircraft(
            id='TEST001',
            model='Boeing 737',
            size=AircraftSize.MEDIUM,
            status=AircraftStatus.IN_AIR
        )
        db.session.add(aircraft)
        db.session.commit()
        return aircraft

@pytest.fixture
def sample_runway(app):
    """Create sample runway"""
    with app.app_context():
        runway = Runway(
            name='RW-TEST',
            length=3000,
            status=RunwayStatus.AVAILABLE
        )
        db.session.add(runway)
        db.session.commit()
        return runway

def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'

def test_create_aircraft(client):
    """Test creating aircraft"""
    response = client.post('/api/aircraft', json={
        'id': 'TEST002',
        'model': 'Airbus A320',
        'size': 'Medium',
        'status': 'Parked'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['id'] == 'TEST002'

def test_runway_length_constraint(app, sample_aircraft):
    """Test runway length constraint"""
    with app.app_context():
        # Create short runway (not suitable for medium aircraft)
        short_runway = Runway(name='SHORT', length=1800, status=RunwayStatus.AVAILABLE)
        db.session.add(short_runway)
        db.session.commit()

        aircraft = Aircraft.query.get('TEST001')
        runway = Runway.query.filter_by(name='SHORT').first()

        is_valid, error = ConstraintService.validate_runway_assignment(aircraft, runway)
        assert not is_valid
        assert 'too short' in error.lower()

def test_runway_occupied_constraint(app, sample_aircraft, sample_runway):
    """Test runway occupied constraint"""
    with app.app_context():
        runway = Runway.query.filter_by(name='RW-TEST').first()
        runway.status = RunwayStatus.OCCUPIED
        runway.occupied_by = 'OTHER001'
        db.session.commit()

        aircraft = Aircraft.query.get('TEST001')
        runway = Runway.query.filter_by(name='RW-TEST').first()

        is_valid, error = ConstraintService.validate_runway_assignment(aircraft, runway)
        assert not is_valid
        assert 'occupied' in error.lower()

def test_landing_queue_fifo(app, sample_aircraft):
    """Test landing queue FIFO ordering"""
    with app.app_context():
        # Add multiple aircraft to queue
        aircraft_ids = ['TEST001', 'TEST002', 'TEST003']

        for aid in aircraft_ids:
            if aid != 'TEST001':  # TEST001 already exists
                aircraft = Aircraft(
                    id=aid,
                    model='Boeing 737',
                    size=AircraftSize.MEDIUM,
                    status=AircraftStatus.IN_AIR
                )
                db.session.add(aircraft)
        db.session.commit()

        # Add to queue
        for aid in aircraft_ids:
            QueueService.add_to_landing_queue(aid)

        # Check order
        next_item = QueueService.get_next_in_queue()
        assert next_item.aircraft_id == 'TEST001'
        assert next_item.priority == 1

def test_conflict_detection_runway(app):
    """Test conflict detection for runway multi-assignment"""
    with app.app_context():
        # Create runway
        runway = Runway(name='CONFLICT-RW', length=3000, status=RunwayStatus.AVAILABLE)
        db.session.add(runway)
        db.session.commit()

        # Create two aircraft assigned to same runway
        aircraft1 = Aircraft(
            id='CONF001',
            model='Boeing 737',
            size=AircraftSize.MEDIUM,
            status=AircraftStatus.LANDING,
            current_runway_id=runway.id
        )
        aircraft2 = Aircraft(
            id='CONF002',
            model='Airbus A320',
            size=AircraftSize.MEDIUM,
            status=AircraftStatus.TAKEOFF,
            current_runway_id=runway.id
        )
        db.session.add_all([aircraft1, aircraft2])
        db.session.commit()

        # Detect conflicts
        conflicts = ConflictDetectionService.check_runway_conflicts()
        assert len(conflicts) > 0
        assert conflicts[0]['type'] == 'runway_multi_assign'
        assert conflicts[0]['severity'] == 'CRITICAL'
