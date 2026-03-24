from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import os
from config import config
from models import db, Aircraft, Runway, Taxiway, Gate, Flight, LandingQueue, TakeoffQueue, \
    AircraftSize, AircraftStatus, RunwayStatus
from services import ConstraintService, ConflictDetectionService, QueueService, TakeoffQueueService, ConstraintService
import threading

LANDING_DURATION_SECONDS = 10
TAXIING_DURATION_SECONDS = 8
TAKEOFF_TAXI_DURATION_SECONDS = 8


def move_aircraft_to_taxiing(aircraft_id):
    with app.app_context():
        try:
            aircraft = Aircraft.query.get(aircraft_id)
            if not aircraft:
                return

            if aircraft.status != AircraftStatus.LANDING:
                return

            aircraft.status = AircraftStatus.TAXIING_TO_GATE
            db.session.commit()

            timer = threading.Timer(TAXIING_DURATION_SECONDS, complete_auto_landing, args=[aircraft_id])
            timer.daemon = True
            timer.start()

        except Exception as e:
            db.session.rollback()
            print(f"Error moving aircraft {aircraft_id} to taxiing: {e}")


def complete_auto_landing(aircraft_id):
    with app.app_context():
        try:
            aircraft = Aircraft.query.get(aircraft_id)
            if not aircraft:
                return

            runway = None
            if aircraft.current_runway_id:
                runway = Runway.query.get(aircraft.current_runway_id)

            if aircraft.status != AircraftStatus.TAXIING_TO_GATE:
                return

            aircraft.status = AircraftStatus.PARKED
            aircraft.current_runway_id = None
            aircraft.altitude = 0
            aircraft.speed = 0

            if runway:
                runway.status = RunwayStatus.AVAILABLE
                runway.occupied_by = None

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print(f"Error completing auto-landing for aircraft {aircraft_id}: {e}")

def complete_auto_takeoff(aircraft_id):
    with app.app_context():
        try:
            aircraft = Aircraft.query.get(aircraft_id)
            if not aircraft:
                return

            runway = None
            if aircraft.current_runway_id:
                runway = Runway.query.get(aircraft.current_runway_id)

            if aircraft.status != AircraftStatus.TAXIING_TO_RUNWAY:
                return

            aircraft.status = AircraftStatus.IN_AIR
            aircraft.current_runway_id = None

            # Optional: set realistic values for takeoff
            aircraft.altitude = 1000
            aircraft.speed = 180

            if runway:
                runway.status = RunwayStatus.AVAILABLE
                runway.occupied_by = None

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print(f"Error completing auto-takeoff for aircraft {aircraft_id}: {e}")

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # Create tables
    with app.app_context():
        db.create_all()

    # ── Health check ─────────────────────────────────────────────────────────
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

    # ── Aircraft endpoints ───────────────────────────────────────────────────
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

        is_valid, error = ConstraintService.validate_aircraft_status_transition(aircraft.status, new_status)
        if not is_valid:
            return jsonify({'error': error}), 400

        aircraft.status = new_status
        aircraft.altitude = data.get('altitude', aircraft.altitude)
        aircraft.speed = data.get('speed', aircraft.speed)
        db.session.commit()
        return jsonify(aircraft.to_dict())

    # ── Runway endpoints ─────────────────────────────────────────────────────
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
        data = request.json
        aircraft_id = data.get('aircraft_id')
        aircraft = Aircraft.query.get_or_404(aircraft_id)
        runway = Runway.query.get_or_404(runway_id)

        is_valid, error = ConstraintService.validate_runway_assignment(aircraft, runway)
        if not is_valid:
            return jsonify({'error': error}), 400

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
        runway = Runway.query.get_or_404(runway_id)
        if runway.occupied_by:
            aircraft = Aircraft.query.get(runway.occupied_by)
            if aircraft:
                aircraft.current_runway_id = None
        runway.status = RunwayStatus.AVAILABLE
        runway.occupied_by = None
        db.session.commit()
        return jsonify({'message': f'Runway {runway.name} released', 'runway': runway.to_dict()})

    # ── Gate endpoints ───────────────────────────────────────────────────────
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

    # ── Taxiway endpoints ────────────────────────────────────────────────────
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

    # ── Flight endpoints ─────────────────────────────────────────────────────
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

    # ── Landing Queue endpoints ──────────────────────────────────────────────
    @app.route('/api/landing-queue', methods=['GET'])
    def get_landing_queue():
        queue = LandingQueue.query.order_by(LandingQueue.priority).all()
        return jsonify([q.to_dict() for q in queue])

    @app.route('/api/landing-queue', methods=['POST'])
    def add_to_landing_queue():
        data = request.json
        aircraft_id = data['aircraft_id']

        aircraft = Aircraft.query.get_or_404(aircraft_id)
        if aircraft.status not in [AircraftStatus.IN_AIR, AircraftStatus.LANDING]:
            return jsonify({
                'error': f'Aircraft must be in air to join landing queue (current status: {aircraft.status.value})'
            }), 400

        # ── Parse optional scheduled_landing_time ────────────────────────────
        scheduled_landing_time = None
        if data.get('scheduled_landing_time'):
            try:
                scheduled_landing_time = datetime.fromisoformat(data['scheduled_landing_time'])
            except ValueError:
                return jsonify({'error': 'Invalid scheduled_landing_time format. Use ISO 8601.'}), 400
        # ────────────────────────────────────────────────────────────────────

        queue_item = QueueService.add_to_landing_queue(aircraft_id, scheduled_landing_time)
        return jsonify({
            'message': f'Aircraft {aircraft_id} added to landing queue',
            'queue_item': queue_item.to_dict()
        }), 201

    @app.route('/api/landing-queue/process-next', methods=['POST'])
    def process_next_landing():
        try:
            next_item = LandingQueue.query.order_by(LandingQueue.priority).first()

            if not next_item:
                return jsonify({'error': 'No aircraft in landing queue'}), 404

            now = datetime.now()
            if next_item.scheduled_landing_time and next_item.scheduled_landing_time > now:
                return jsonify({
                    'error': f'Aircraft {next_item.aircraft_id} is scheduled for '
                            f'{next_item.scheduled_landing_time.strftime("%Y-%m-%d %I:%M %p")} '
                            f'and cannot be processed yet'
                }), 400

            aircraft = Aircraft.query.get(next_item.aircraft_id)
            if not aircraft:
                db.session.delete(next_item)
                db.session.commit()
                return jsonify({'error': 'Aircraft not found; removed invalid queue entry'}), 404

            runways = Runway.query.all()
            failure_reasons = []
            suitable_runway = None

            for runway in runways:
                is_valid, error = ConstraintService.validate_runway_assignment(aircraft, runway)
                if is_valid:
                    suitable_runway = runway
                    break
                failure_reasons.append(f"{runway.name}: {error}")

            if not suitable_runway:
                return jsonify({
                    'error': 'No suitable runway available',
                    'details': failure_reasons
                }), 400

            suitable_runway.status = RunwayStatus.OCCUPIED
            suitable_runway.occupied_by = aircraft.id
            suitable_runway.last_used = datetime.now()

            aircraft.status = AircraftStatus.LANDING
            aircraft.current_runway_id = suitable_runway.id

            timer = threading.Timer(LANDING_DURATION_SECONDS, move_aircraft_to_taxiing, args=[aircraft.id])
            timer.daemon = True
            timer.start()

            db.session.delete(next_item)

            remaining_queue = LandingQueue.query.order_by(LandingQueue.priority).all()
            for idx, item in enumerate(remaining_queue, start=1):
                item.priority = idx

            db.session.commit()

            return jsonify({
                'message': f'Aircraft {aircraft.id} cleared to land on runway {suitable_runway.name}',
                'aircraft_id': aircraft.id,
                'runway_id': suitable_runway.id,
                'runway_name': suitable_runway.name,
                'new_status': aircraft.status.value
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/landing-queue/<aircraft_id>', methods=['DELETE'])
    def remove_from_landing_queue(aircraft_id):
        success = QueueService.remove_from_queue(aircraft_id)
        if not success:
            return jsonify({'error': f'Aircraft {aircraft_id} not found in landing queue'}), 404
        return jsonify({'message': f'Aircraft {aircraft_id} removed from landing queue'})

    @app.route('/api/aircraft/<aircraft_id>/complete-landing', methods=['POST'])
    def complete_landing(aircraft_id):
        try:
            aircraft = Aircraft.query.get(aircraft_id)

            if not aircraft:
                return jsonify({'error': 'Aircraft not found'}), 404

            if aircraft.status != AircraftStatus.LANDING:
                return jsonify({'error': f'Aircraft {aircraft_id} is not currently landing'}), 400

            runway = None
            if aircraft.current_runway_id:
                runway = Runway.query.get(aircraft.current_runway_id)

            # Update aircraft
            aircraft.status = AircraftStatus.PARKED
            aircraft.current_runway_id = None
            aircraft.altitude = 0
            aircraft.speed = 0

            # Release runway if assigned
            if runway:
                runway.status = RunwayStatus.AVAILABLE
                runway.occupied_by = None
                # keep last_used as-is so cooldown still works if you want that behavior

            db.session.commit()

            return jsonify({
                'message': f'Aircraft {aircraft.id} has completed landing and is now parked',
                'aircraft_id': aircraft.id,
                'new_status': aircraft.status.value,
                'released_runway': runway.name if runway else None
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500


    # ── Takeoff Queue endpoints (NEW) ────────────────────────────────────────
    @app.route('/api/takeoff-queue', methods=['GET'])
    def get_takeoff_queue():
        queue = TakeoffQueue.query.order_by(TakeoffQueue.priority).all()
        return jsonify([q.to_dict() for q in queue])

    @app.route('/api/takeoff-queue', methods=['POST'])
    def add_to_takeoff_queue():
        try:
            data = request.get_json()
            aircraft_id = data.get('aircraft_id')

            if not aircraft_id:
                return jsonify({'error': 'aircraft_id is required'}), 400

            aircraft = Aircraft.query.get(aircraft_id)
            if not aircraft:
                return jsonify({'error': 'Aircraft not found'}), 404

            if aircraft.status != AircraftStatus.PARKED:
                return jsonify({'error': f'Aircraft {aircraft_id} must be Parked to request takeoff'}), 400

            existing = TakeoffQueue.query.filter_by(aircraft_id=aircraft_id).first()
            if existing:
                return jsonify({'error': f'Aircraft {aircraft_id} is already in takeoff queue'}), 400

            next_priority = (db.session.query(db.func.max(TakeoffQueue.priority)).scalar() or 0) + 1

            queue_item = TakeoffQueue(
                aircraft_id=aircraft_id,
                priority=next_priority
            )

            db.session.add(queue_item)
            db.session.commit()

            return jsonify({
                'message': f'Aircraft {aircraft_id} added to takeoff queue',
                'queue_position': next_priority
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/takeoff-queue/process-next', methods=['POST'])
    def process_next_takeoff():
        try:
            next_item = TakeoffQueue.query.order_by(TakeoffQueue.priority).first()

            if not next_item:
                return jsonify({'error': 'No aircraft in takeoff queue'}), 404

            aircraft = Aircraft.query.get(next_item.aircraft_id)
            if not aircraft:
                db.session.delete(next_item)
                db.session.commit()
                return jsonify({'error': 'Aircraft not found; removed invalid queue entry'}), 404

            runways = Runway.query.all()
            failure_reasons = []
            suitable_runway = None

            for runway in runways:
                is_valid, error = ConstraintService.validate_runway_assignment(aircraft, runway)
                if is_valid:
                    suitable_runway = runway
                    break
                failure_reasons.append(f"{runway.name}: {error}")

            if not suitable_runway:
                return jsonify({
                    'error': 'No suitable runway available',
                    'details': failure_reasons
                }), 400

            suitable_runway.status = RunwayStatus.OCCUPIED
            suitable_runway.occupied_by = aircraft.id
            suitable_runway.last_used = datetime.now()

            aircraft.status = AircraftStatus.TAXIING_TO_RUNWAY
            aircraft.current_runway_id = suitable_runway.id

            # Optional: realistic values while taxiing
            aircraft.altitude = 0
            aircraft.speed = 20

            db.session.delete(next_item)

            remaining_queue = TakeoffQueue.query.order_by(TakeoffQueue.priority).all()
            for idx, item in enumerate(remaining_queue, start=1):
                item.priority = idx

            db.session.commit()

            timer = threading.Timer(TAKEOFF_TAXI_DURATION_SECONDS, complete_auto_takeoff, args=[aircraft.id])
            timer.daemon = True
            timer.start()

            return jsonify({
                'message': f'Aircraft {aircraft.id} cleared for takeoff on runway {suitable_runway.name}',
                'aircraft_id': aircraft.id,
                'runway_id': suitable_runway.id,
                'runway_name': suitable_runway.name,
                'new_status': aircraft.status.value
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/takeoff-queue/<aircraft_id>', methods=['DELETE'])
    def remove_from_takeoff_queue(aircraft_id):
        success = TakeoffQueueService.remove_from_queue(aircraft_id)
        if not success:
            return jsonify({'error': f'Aircraft {aircraft_id} not found in takeoff queue'}), 404
        return jsonify({'message': f'Aircraft {aircraft_id} removed from takeoff queue'})
    # ────────────────────────────────────────────────────────────────────────

    # ── Conflict Detection ───────────────────────────────────────────────────
    @app.route('/api/conflicts', methods=['GET'])
    def get_conflicts():
        conflicts = ConflictDetectionService.detect_all_conflicts()
        return jsonify({
            'conflicts': conflicts,
            'count': len(conflicts),
            'has_critical': any(c.get('severity') == 'CRITICAL' for c in conflicts)
        })

    # ── Dashboard ────────────────────────────────────────────────────────────
    @app.route('/api/dashboard', methods=['GET'])
    def get_dashboard():
        aircraft = Aircraft.query.all()
        runways = Runway.query.all()
        gates = Gate.query.all()
        landing_queue = LandingQueue.query.order_by(LandingQueue.priority).all()
        takeoff_queue = TakeoffQueue.query.order_by(TakeoffQueue.priority).all()
        conflicts = ConflictDetectionService.detect_all_conflicts()

        return jsonify({
            'aircraft': {
                'total': len(aircraft),
                'in_air': len([a for a in aircraft if a.status == AircraftStatus.IN_AIR]),
                'landing': len([a for a in aircraft if a.status == AircraftStatus.LANDING]),
                'taxiing_to_gate': len([a for a in aircraft if a.status == AircraftStatus.TAXIING_TO_GATE]),
                'taxiing_to_runway': len([a for a in aircraft if a.status == AircraftStatus.TAXIING_TO_RUNWAY]),
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
            # NEW
            'takeoff_queue': {
                'count': len(takeoff_queue),
                'queue': [q.to_dict() for q in takeoff_queue]
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