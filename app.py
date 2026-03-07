from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import os

from config import config
from models import db, Aircraft, Runway, Taxiway, Gate, Flight, LandingQueue, AircraftSize, AircraftStatus, RunwayStatus
from services import ConstraintService, ConflictDetectionService, QueueService

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # Create tables
    with app.app_context():
        db.create_all()

    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

    # Aircraft endpoints
    @app.route('/api/aircraft', methods=['GET'])
    def get_aircraft():
        aircraft = Aircraft.query.all()
        return jsonify([a.to_dict() for a in aircraft])

    @app.route('/api/aircraft/<aircraft_id>', methods=['GET'])
    def get_aircraft_by_id(aircraft_id):
        aircraft = Aircraft.query.get_or_404(aircraft_id)
        return jsonify(aircraft.to_dict())

    @app.route('/api/aircraft', methods=['POST'])
    def create_aircraft():
        data = request.json

        aircraft = Aircraft(
            id=data['id'],
            model=data['model'],
            size=AircraftSize[data['size'].upper()],
            status=AircraftStatus[data.get('status', 'PARKED').upper().replace('-', '_')],
            altitude=data.get('altitude', 0),
            speed=data.get('speed', 0)
        )

        db.session.add(aircraft)
        db.session.commit()

        return jsonify(aircraft.to_dict()), 201

    @app.route('/api/aircraft/<aircraft_id>/status', methods=['PUT'])
    def update_aircraft_status(aircraft_id):
        aircraft = Aircraft.query.get_or_404(aircraft_id)
        data = request.json

        new_status = AircraftStatus[data['status'].upper().replace('-', '_')]

        # Validate status transition
        is_valid, error = ConstraintService.validate_aircraft_status_transition(aircraft.status, new_status)
        if not is_valid:
            return jsonify({'error': error}), 400

        aircraft.status = new_status
        aircraft.altitude = data.get('altitude', aircraft.altitude)
        aircraft.speed = data.get('speed', aircraft.speed)

        db.session.commit()

        return jsonify(aircraft.to_dict())

    # Runway endpoints
    @app.route('/api/runways', methods=['GET'])
    def get_runways():
        runways = Runway.query.all()
        return jsonify([r.to_dict() for r in runways])

    @app.route('/api/runways/<int:runway_id>', methods=['GET'])
    def get_runway(runway_id):
        runway = Runway.query.get_or_404(runway_id)
        return jsonify(runway.to_dict())

    @app.route('/api/runways', methods=['POST'])
    def create_runway():
        data = request.json

        runway = Runway(
            name=data['name'],
            length=data['length'],
            status=RunwayStatus[data.get('status', 'AVAILABLE').upper()]
        )

        db.session.add(runway)
        db.session.commit()

        return jsonify(runway.to_dict()), 201

    @app.route('/api/runways/<int:runway_id>/assign', methods=['POST'])
    def assign_runway(runway_id):
        """Assign a runway to an aircraft"""
        data = request.json
        aircraft_id = data.get('aircraft_id')

        aircraft = Aircraft.query.get_or_404(aircraft_id)
        runway = Runway.query.get_or_404(runway_id)

        # Validate assignment
        is_valid, error = ConstraintService.validate_runway_assignment(aircraft, runway)
        if not is_valid:
            return jsonify({'error': error}), 400

        # Assign runway
        runway.status = RunwayStatus.OCCUPIED
        runway.occupied_by = aircraft.id
        runway.last_used = datetime.utcnow()
        aircraft.current_runway_id = runway.id

        db.session.commit()

        return jsonify({
            'message': f'Runway {runway.name} assigned to aircraft {aircraft.id}',
            'runway': runway.to_dict(),
            'aircraft': aircraft.to_dict()
        })

    @app.route('/api/runways/<int:runway_id>/release', methods=['POST'])
    def release_runway(runway_id):
        """Release a runway after aircraft has finished using it"""
        runway = Runway.query.get_or_404(runway_id)

        if runway.occupied_by:
            aircraft = Aircraft.query.get(runway.occupied_by)
            if aircraft:
                aircraft.current_runway_id = None

        runway.status = RunwayStatus.AVAILABLE
        runway.occupied_by = None

        db.session.commit()

        return jsonify({
            'message': f'Runway {runway.name} released',
            'runway': runway.to_dict()
        })

    # Gate endpoints
    @app.route('/api/gates', methods=['GET'])
    def get_gates():
        gates = Gate.query.all()
        return jsonify([g.to_dict() for g in gates])

    @app.route('/api/gates', methods=['POST'])
    def create_gate():
        data = request.json
        gate = Gate(name=data['name'])
        db.session.add(gate)
        db.session.commit()
        return jsonify(gate.to_dict()), 201

    # Taxiway endpoints
    @app.route('/api/taxiways', methods=['GET'])
    def get_taxiways():
        taxiways = Taxiway.query.all()
        return jsonify([t.to_dict() for t in taxiways])

    @app.route('/api/taxiways', methods=['POST'])
    def create_taxiway():
        data = request.json
        taxiway = Taxiway(name=data['name'])
        db.session.add(taxiway)
        db.session.commit()
        return jsonify(taxiway.to_dict()), 201

    # Flight endpoints
    @app.route('/api/flights', methods=['GET'])
    def get_flights():
        flights = Flight.query.all()
        return jsonify([f.to_dict() for f in flights])

    @app.route('/api/flights', methods=['POST'])
    def create_flight():
        data = request.json

        flight = Flight(
            flight_number=data['flight_number'],
            aircraft_id=data['aircraft_id'],
            scheduled_departure=datetime.fromisoformat(data['scheduled_departure']),
            scheduled_arrival=datetime.fromisoformat(data['scheduled_arrival']),
            origin=data['origin'],
            destination=data['destination'],
            status=data.get('status', 'Scheduled')
        )

        db.session.add(flight)
        db.session.commit()

        return jsonify(flight.to_dict()), 201

    # Landing Queue endpoints
    @app.route('/api/landing-queue', methods=['GET'])
    def get_landing_queue():
        queue = LandingQueue.query.order_by(LandingQueue.priority).all()
        return jsonify([q.to_dict() for q in queue])

    @app.route('/api/landing-queue', methods=['POST'])
    def add_to_landing_queue():
        data = request.json
        aircraft_id = data['aircraft_id']

        # Validate aircraft exists and is in air
        aircraft = Aircraft.query.get_or_404(aircraft_id)
        if aircraft.status not in [AircraftStatus.IN_AIR, AircraftStatus.LANDING]:
            return jsonify({'error': f'Aircraft must be in air to join landing queue (current status: {aircraft.status.value})'}), 400

        queue_item = QueueService.add_to_landing_queue(aircraft_id)

        return jsonify({
            'message': f'Aircraft {aircraft_id} added to landing queue',
            'queue_item': queue_item.to_dict()
        }), 201

    @app.route('/api/landing-queue/process-next', methods=['POST'])
    def process_next_in_queue():
        """Process next aircraft in landing queue and assign runway"""
        queue_item, error = QueueService.assign_runway_to_next()

        if error:
            return jsonify({'error': error}), 400

        return jsonify({
            'message': 'Runway assigned to next aircraft in queue',
            'queue_item': queue_item.to_dict()
        })

    @app.route('/api/landing-queue/<aircraft_id>', methods=['DELETE'])
    def remove_from_landing_queue(aircraft_id):
        success = QueueService.remove_from_queue(aircraft_id)

        if not success:
            return jsonify({'error': f'Aircraft {aircraft_id} not found in queue'}), 404

        return jsonify({'message': f'Aircraft {aircraft_id} removed from landing queue'})

    # Conflict Detection endpoints
    @app.route('/api/conflicts', methods=['GET'])
    def get_conflicts():
        conflicts = ConflictDetectionService.detect_all_conflicts()
        return jsonify({
            'conflicts': conflicts,
            'count': len(conflicts),
            'has_critical': any(c.get('severity') == 'CRITICAL' for c in conflicts)
        })

    # Dashboard endpoint (aggregate data for controller)
    @app.route('/api/dashboard', methods=['GET'])
    def get_dashboard():
        aircraft = Aircraft.query.all()
        runways = Runway.query.all()
        gates = Gate.query.all()
        landing_queue = LandingQueue.query.order_by(LandingQueue.priority).all()
        conflicts = ConflictDetectionService.detect_all_conflicts()

        return jsonify({
            'aircraft': {
                'total': len(aircraft),
                'in_air': len([a for a in aircraft if a.status == AircraftStatus.IN_AIR]),
                'landing': len([a for a in aircraft if a.status == AircraftStatus.LANDING]),
                'taxiing': len([a for a in aircraft if a.status == AircraftStatus.TAXIING]),
                'parked': len([a for a in aircraft if a.status == AircraftStatus.PARKED]),
                'list': [a.to_dict() for a in aircraft]
            },
            'runways': {
                'total': len(runways),
                'available': len([r for r in runways if r.status == RunwayStatus.AVAILABLE]),
                'occupied': len([r for r in runways if r.status == RunwayStatus.OCCUPIED]),
                'list': [r.to_dict() for r in runways]
            },
            'gates': {
                'total': len(gates),
                'available': len([g for g in gates if g.status == RunwayStatus.AVAILABLE]),
                'occupied': len([g for g in gates if g.status == RunwayStatus.OCCUPIED]),
            },
            'landing_queue': {
                'count': len(landing_queue),
                'queue': [q.to_dict() for q in landing_queue]
            },
            'conflicts': {
                'count': len(conflicts),
                'has_critical': any(c.get('severity') == 'CRITICAL' for c in conflicts),
                'list': conflicts
            }
        })

    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
