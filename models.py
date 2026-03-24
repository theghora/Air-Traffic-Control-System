from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum

db = SQLAlchemy()

class AircraftSize(str, Enum):
    SMALL = "Small"
    MEDIUM = "Medium"
    HEAVY = "Heavy"

class AircraftStatus(Enum):
    PARKED = "Parked"
    TAXIING_TO_GATE = "Taxiing-To-Gate"
    TAXIING_TO_RUNWAY = "Taxiing-To-Runway"
    IN_AIR = "In-Air"
    LANDING = "Landing"

class RunwayStatus(str, Enum):
    AVAILABLE = "Available"
    OCCUPIED = "Occupied"
    MAINTENANCE = "Maintenance"

class Aircraft(db.Model):
    __tablename__ = 'aircraft'

    id = db.Column(db.String(10), primary_key=True)
    model = db.Column(db.String(50), nullable=False)
    size = db.Column(db.Enum(AircraftSize), nullable=False)
    status = db.Column(db.Enum(AircraftStatus), nullable=False, default=AircraftStatus.PARKED)
    current_runway_id = db.Column(db.Integer, db.ForeignKey('runway.id'), nullable=True)
    current_gate_id = db.Column(db.Integer, db.ForeignKey('gate.id'), nullable=True)
    altitude = db.Column(db.Integer, default=0)  # in feet
    speed = db.Column(db.Integer, default=0)     # in knots
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    flights = db.relationship('Flight', backref='aircraft', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'model': self.model,
            'size': self.size.value,
            'status': self.status.value,
            'current_runway_id': self.current_runway_id,
            'current_gate_id': self.current_gate_id,
            'altitude': self.altitude,
            'speed': self.speed,
            'last_updated': self.last_updated.isoformat()
        }

class Runway(db.Model):
    __tablename__ = 'runway'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)
    length = db.Column(db.Integer, nullable=False)  # in meters
    status = db.Column(db.Enum(RunwayStatus), nullable=False, default=RunwayStatus.AVAILABLE)
    occupied_by = db.Column(db.String(10), db.ForeignKey('aircraft.id'), nullable=True)
    last_used = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'length': self.length,
            'status': self.status.value,
            'occupied_by': self.occupied_by,
            'last_used': self.last_used.isoformat() if self.last_used else None
        }

    def is_suitable_for_aircraft(self, aircraft_size):
        """Check if runway length is suitable for aircraft size"""
        from config import Config
        min_length = {
            AircraftSize.SMALL: Config.RUNWAY_LENGTH_SMALL,
            AircraftSize.MEDIUM: Config.RUNWAY_LENGTH_MEDIUM,
            AircraftSize.HEAVY: Config.RUNWAY_LENGTH_HEAVY
        }
        return self.length >= min_length.get(aircraft_size, 0)

class Taxiway(db.Model):
    __tablename__ = 'taxiway'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)
    status = db.Column(db.Enum(RunwayStatus), nullable=False, default=RunwayStatus.AVAILABLE)
    occupied_by = db.Column(db.String(10), db.ForeignKey('aircraft.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status.value,
            'occupied_by': self.occupied_by
        }

class Gate(db.Model):
    __tablename__ = 'gate'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)
    status = db.Column(db.Enum(RunwayStatus), nullable=False, default=RunwayStatus.AVAILABLE)
    occupied_by = db.Column(db.String(10), db.ForeignKey('aircraft.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status.value,
            'occupied_by': self.occupied_by
        }

class Flight(db.Model):
    __tablename__ = 'flight'

    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(10), unique=True, nullable=False)
    aircraft_id = db.Column(db.String(10), db.ForeignKey('aircraft.id'), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=True)
    arrival_time = db.Column(db.DateTime, nullable=True)
    scheduled_departure = db.Column(db.DateTime, nullable=False)
    scheduled_arrival = db.Column(db.DateTime, nullable=False)
    origin = db.Column(db.String(50), nullable=False)
    destination = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Scheduled')
    assigned_runway_id = db.Column(db.Integer, db.ForeignKey('runway.id'), nullable=True)
    assigned_gate_id = db.Column(db.Integer, db.ForeignKey('gate.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'flight_number': self.flight_number,
            'aircraft_id': self.aircraft_id,
            'departure_time': self.departure_time.isoformat() if self.departure_time else None,
            'arrival_time': self.arrival_time.isoformat() if self.arrival_time else None,
            'scheduled_departure': self.scheduled_departure.isoformat(),
            'scheduled_arrival': self.scheduled_arrival.isoformat(),
            'origin': self.origin,
            'destination': self.destination,
            'status': self.status,
            'assigned_runway_id': self.assigned_runway_id,
            'assigned_gate_id': self.assigned_gate_id
        }

class LandingQueue(db.Model):
    __tablename__ = 'landing_queue'

    id = db.Column(db.Integer, primary_key=True)
    aircraft_id = db.Column(db.String(10), db.ForeignKey('aircraft.id'), nullable=False)
    priority = db.Column(db.Integer, nullable=False)  # Lower number = higher priority
    requested_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    # ── NEW: optional scheduled landing time set by the controller ──────────
    scheduled_landing_time = db.Column(db.DateTime, nullable=True)
    # ────────────────────────────────────────────────────────────────────────
    assigned_runway_id = db.Column(db.Integer, db.ForeignKey('runway.id'), nullable=True)

    # Relationships
    aircraft = db.relationship('Aircraft', foreign_keys=[aircraft_id])
    runway = db.relationship('Runway', foreign_keys=[assigned_runway_id])

    def to_dict(self):
        return {
            'id': self.id,
            'aircraft_id': self.aircraft_id,
            'priority': self.priority,
            'requested_at': self.requested_at.isoformat(),
            'scheduled_landing_time': self.scheduled_landing_time.isoformat() if self.scheduled_landing_time else None,
            'assigned_runway_id': self.assigned_runway_id
        }


# ── NEW: Takeoff Queue model ─────────────────────────────────────────────────
class TakeoffQueue(db.Model):
    __tablename__ = 'takeoff_queue'

    id = db.Column(db.Integer, primary_key=True)
    aircraft_id = db.Column(db.String(10), db.ForeignKey('aircraft.id'), nullable=False)
    priority = db.Column(db.Integer, nullable=False)  # Lower number = higher priority (FIFO)
    requested_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    assigned_runway_id = db.Column(db.Integer, db.ForeignKey('runway.id'), nullable=True)

    # Relationships
    aircraft = db.relationship('Aircraft', foreign_keys=[aircraft_id])
    runway = db.relationship('Runway', foreign_keys=[assigned_runway_id])

    def to_dict(self):
        return {
            'id': self.id,
            'aircraft_id': self.aircraft_id,
            'priority': self.priority,
            'requested_at': self.requested_at.isoformat(),
            'assigned_runway_id': self.assigned_runway_id
        }
# ─────────────────────────────────────────────────────────────────────────────