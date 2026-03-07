from datetime import datetime, timedelta
from models import db, Aircraft, Runway, Flight, LandingQueue, AircraftSize, RunwayStatus, AircraftStatus
from config import Config

class ConstraintService:
    """Service for validating ATC constraints"""

    @staticmethod
    def validate_runway_assignment(aircraft, runway):
        """
        Validate if an aircraft can be assigned to a runway
        Returns: (is_valid, error_message)
        """
        # Check if runway is available
        if runway.status != RunwayStatus.AVAILABLE:
            return False, f"Runway {runway.name} is not available (Status: {runway.status.value})"

        # Check if runway is occupied
        if runway.occupied_by and runway.occupied_by != aircraft.id:
            return False, f"Runway {runway.name} is occupied by aircraft {runway.occupied_by}"

        # Check runway length requirement
        if not runway.is_suitable_for_aircraft(aircraft.size):
            required_length = {
                AircraftSize.SMALL: Config.RUNWAY_LENGTH_SMALL,
                AircraftSize.MEDIUM: Config.RUNWAY_LENGTH_MEDIUM,
                AircraftSize.HEAVY: Config.RUNWAY_LENGTH_HEAVY
            }
            return False, f"Runway {runway.name} (length: {runway.length}m) is too short for {aircraft.size.value} aircraft (requires: {required_length[aircraft.size]}m)"

        # Check cooldown period
        if runway.last_used:
            time_since_use = datetime.utcnow() - runway.last_used
            if time_since_use.total_seconds() < Config.RUNWAY_COOLDOWN_SECONDS:
                remaining = Config.RUNWAY_COOLDOWN_SECONDS - int(time_since_use.total_seconds())
                return False, f"Runway {runway.name} is in cooldown period ({remaining}s remaining)"

        return True, None

    @staticmethod
    def find_suitable_runway(aircraft):
        """Find the first available suitable runway for an aircraft"""
        runways = Runway.query.filter_by(status=RunwayStatus.AVAILABLE).all()

        for runway in runways:
            is_valid, _ = ConstraintService.validate_runway_assignment(aircraft, runway)
            if is_valid:
                return runway

        return None

    @staticmethod
    def validate_aircraft_status_transition(current_status, new_status):
        """
        Validate if status transition is allowed
        Returns: (is_valid, error_message)
        """
        valid_transitions = {
            AircraftStatus.IN_AIR: [AircraftStatus.LANDING],
            AircraftStatus.LANDING: [AircraftStatus.TAXIING, AircraftStatus.IN_AIR],
            AircraftStatus.TAXIING: [AircraftStatus.PARKED, AircraftStatus.TAKEOFF],
            AircraftStatus.PARKED: [AircraftStatus.TAXIING],
            AircraftStatus.TAKEOFF: [AircraftStatus.IN_AIR]
        }

        if new_status not in valid_transitions.get(current_status, []):
            return False, f"Invalid status transition from {current_status.value} to {new_status.value}"

        return True, None

class ConflictDetectionService:
    """Service for detecting conflicts in ATC operations"""

    @staticmethod
    def check_runway_conflicts():
        """Check for runway assignment conflicts"""
        conflicts = []

        # Find runways with multiple aircraft assigned
        runways = Runway.query.all()
        for runway in runways:
            aircraft_on_runway = Aircraft.query.filter_by(current_runway_id=runway.id).all()
            if len(aircraft_on_runway) > 1:
                conflicts.append({
                    'type': 'runway_multi_assign',
                    'runway': runway.name,
                    'aircraft': [a.id for a in aircraft_on_runway],
                    'severity': 'CRITICAL'
                })

        return conflicts

    @staticmethod
    def check_landing_queue_conflicts():
        """Check for conflicts in landing queue"""
        conflicts = []

        # Check for duplicate priority assignments
        queue_items = LandingQueue.query.order_by(LandingQueue.priority).all()
        priorities = [item.priority for item in queue_items]

        if len(priorities) != len(set(priorities)):
            conflicts.append({
                'type': 'duplicate_priority',
                'message': 'Multiple aircraft have the same landing priority',
                'severity': 'HIGH'
            })

        # Check for aircraft in queue but not in air
        for item in queue_items:
            aircraft = Aircraft.query.get(item.aircraft_id)
            if aircraft and aircraft.status not in [AircraftStatus.IN_AIR, AircraftStatus.LANDING]:
                conflicts.append({
                    'type': 'invalid_queue_status',
                    'aircraft_id': aircraft.id,
                    'status': aircraft.status.value,
                    'message': f'Aircraft {aircraft.id} in landing queue but status is {aircraft.status.value}',
                    'severity': 'MEDIUM'
                })

        return conflicts

    @staticmethod
    def detect_all_conflicts():
        """Run all conflict detection checks"""
        all_conflicts = []
        all_conflicts.extend(ConflictDetectionService.check_runway_conflicts())
        all_conflicts.extend(ConflictDetectionService.check_landing_queue_conflicts())
        return all_conflicts

class QueueService:
    """Service for managing landing/takeoff queues (FIFO)"""

    @staticmethod
    def add_to_landing_queue(aircraft_id):
        """Add aircraft to landing queue with FIFO priority"""
        # Get next priority (highest current priority + 1)
        max_priority = db.session.query(db.func.max(LandingQueue.priority)).scalar() or 0

        queue_item = LandingQueue(
            aircraft_id=aircraft_id,
            priority=max_priority + 1
        )
        db.session.add(queue_item)
        db.session.commit()

        return queue_item

    @staticmethod
    def get_next_in_queue():
        """Get the next aircraft in landing queue (lowest priority number)"""
        return LandingQueue.query.order_by(LandingQueue.priority).first()

    @staticmethod
    def remove_from_queue(aircraft_id):
        """Remove aircraft from landing queue"""
        queue_item = LandingQueue.query.filter_by(aircraft_id=aircraft_id).first()
        if queue_item:
            db.session.delete(queue_item)
            db.session.commit()
            return True
        return False

    @staticmethod
    def assign_runway_to_next():
        """Assign runway to next aircraft in queue if available"""
        next_item = QueueService.get_next_in_queue()
        if not next_item:
            return None, "No aircraft in queue"

        aircraft = Aircraft.query.get(next_item.aircraft_id)
        if not aircraft:
            return None, "Aircraft not found"

        # Find suitable runway
        runway = ConstraintService.find_suitable_runway(aircraft)
        if not runway:
            return None, "No suitable runway available"

        # Assign runway
        next_item.assigned_runway_id = runway.id
        runway.status = RunwayStatus.OCCUPIED
        runway.occupied_by = aircraft.id
        runway.last_used = datetime.utcnow()

        db.session.commit()

        return next_item, None
