# Project Structure - Air Traffic Control System

## 📁 Directory Overview

```
Air-Traffic-Control-System/
│
├── frontend/                    # Frontend dashboard application
│   ├── index.html              # Main dashboard HTML
│   ├── styles.css              # Dashboard styling
│   └── script.js               # Dashboard JavaScript logic
│
├── app.py                      # Flask application & REST API endpoints
├── models.py                   # Database models & ORM definitions
├── services.py                 # Business logic services
├── config.py                   # Application configuration
├── init_db.py                  # Database initialization script
├── test_atc.py                 # Test suite
│
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
│
├── README.md                   # Main documentation
├── API_DOCUMENTATION.md        # API reference
├── QUICK_START.md             # Quick start guide
└── PROJECT_STRUCTURE.md       # This file
```

## 📄 File Descriptions

### Backend Files

#### `app.py` - Main Application
**Purpose**: Flask application entry point and REST API endpoints

**Key Components**:
- Flask app factory pattern
- API endpoint definitions
- CORS configuration
- Database initialization
- Request/response handling

**Main Endpoints**:
- Health check
- Aircraft CRUD operations
- Runway management
- Landing queue operations
- Conflict detection
- Dashboard data aggregation

**Dependencies**: Flask, Flask-CORS, models, services, config

---

#### `models.py` - Database Models
**Purpose**: SQLAlchemy ORM models defining database schema

**Models Defined**:

1. **Aircraft**
   - Fields: id, model, size, status, altitude, speed, runway_id, gate_id
   - Enums: AircraftSize (Small/Medium/Heavy), AircraftStatus (In-Air/Landing/Taxiing/Parked/Takeoff)
   - Methods: `to_dict()`

2. **Runway**
   - Fields: id, name, length, status, occupied_by, last_used
   - Enum: RunwayStatus (Available/Occupied/Maintenance)
   - Methods: `to_dict()`, `is_suitable_for_aircraft()`

3. **Gate**
   - Fields: id, name, status, occupied_by
   - Methods: `to_dict()`

4. **Taxiway**
   - Fields: id, name, status, occupied_by
   - Methods: `to_dict()`

5. **Flight**
   - Fields: id, flight_number, aircraft_id, departure_time, arrival_time, origin, destination, status
   - Methods: `to_dict()`

6. **LandingQueue**
   - Fields: id, aircraft_id, priority, requested_at, assigned_runway_id
   - Methods: `to_dict()`
   - Relationships: aircraft, runway

**Database Schema**:
```sql
aircraft (id PK, model, size, status, current_runway_id FK, current_gate_id FK, altitude, speed, last_updated)
runway (id PK, name UNIQUE, length, status, occupied_by FK, last_used)
gate (id PK, name UNIQUE, status, occupied_by FK)
taxiway (id PK, name UNIQUE, status, occupied_by FK)
flight (id PK, flight_number UNIQUE, aircraft_id FK, departure_time, arrival_time, scheduled_departure, scheduled_arrival, origin, destination, status, assigned_runway_id FK, assigned_gate_id FK)
landing_queue (id PK, aircraft_id FK, priority, requested_at, assigned_runway_id FK)
```

---

#### `services.py` - Business Logic Services
**Purpose**: Core business logic separated from API layer

**Services Defined**:

1. **ConstraintService**
   - `validate_runway_assignment()`: Check if aircraft can use runway
   - `find_suitable_runway()`: Find available runway for aircraft
   - `validate_aircraft_status_transition()`: Validate state machine transitions

   **Constraints Validated**:
   - Runway availability
   - Runway occupancy
   - Runway length requirements
   - Cooldown period (60 seconds)

2. **ConflictDetectionService**
   - `check_runway_conflicts()`: Detect multiple aircraft on same runway
   - `check_landing_queue_conflicts()`: Validate queue integrity
   - `detect_all_conflicts()`: Run all conflict checks

   **Conflict Types**:
   - Critical: Multiple aircraft on same runway
   - High: Duplicate queue priorities
   - Medium: Invalid aircraft status in queue

3. **QueueService**
   - `add_to_landing_queue()`: Add aircraft with FIFO priority
   - `get_next_in_queue()`: Get aircraft with lowest priority
   - `remove_from_queue()`: Remove aircraft from queue
   - `assign_runway_to_next()`: Assign runway to next in queue

**Design Pattern**: Service layer pattern - separates business logic from presentation

---

#### `config.py` - Configuration
**Purpose**: Application configuration management

**Configuration Classes**:
- `Config`: Base configuration
- `DevelopmentConfig`: Development settings (DEBUG=True, SQLite)
- `ProductionConfig`: Production settings (DEBUG=False, PostgreSQL)

**Key Settings**:
- Database URLs
- Secret keys
- Runway length requirements (1500m/2500m/3500m)
- Runway cooldown period (60s)
- Maximum runway capacity (1 aircraft)

---

#### `init_db.py` - Database Initialization
**Purpose**: Initialize database with sample data for testing

**Sample Data Created**:
- 4 runways (RW-09L, RW-09R, RW-27L, RW-27R) with varying lengths
- 10 gates (G1-G10)
- 5 taxiways (TA-TE)
- 6 aircraft (mix of Small/Medium/Heavy, various statuses)
- 3 flights (scheduled, in-flight)

**Usage**:
```bash
python init_db.py
```

---

#### `test_atc.py` - Test Suite
**Purpose**: Unit and integration tests using pytest

**Test Coverage**:
- API endpoint tests (health, CRUD operations)
- Constraint validation tests
- Conflict detection tests
- Queue FIFO ordering tests
- Status transition tests

**Fixtures**:
- `app`: Test Flask application
- `client`: Test client for API calls
- `sample_aircraft`: Sample aircraft for testing
- `sample_runway`: Sample runway for testing

**Usage**:
```bash
pytest test_atc.py -v
```

---

### Frontend Files

#### `frontend/index.html` - Dashboard HTML
**Purpose**: Main controller dashboard interface

**Sections**:
1. Header with system status
2. Dashboard overview (stat cards)
3. Conflicts section (conditional)
4. Runways status display
5. Aircraft table
6. Landing queue display
7. Modals for adding aircraft/runways

**Key Features**:
- Responsive design
- Real-time updates (5-second polling)
- Interactive controls
- Modal forms for data entry

---

#### `frontend/styles.css` - Dashboard Styling
**Purpose**: Complete styling for controller dashboard

**Design System**:
- Color scheme: Primary blue (#2563eb), Success green (#10b981), Warning amber (#f59e0b), Danger red (#ef4444)
- Typography: System fonts, responsive sizing
- Components: Cards, tables, buttons, modals, badges
- Layout: CSS Grid, Flexbox
- Responsive: Mobile-first approach

**Component Styles**:
- Stat cards with colored left borders
- Runway cards with status indicators
- Aircraft table with status badges
- Queue items with priority circles
- Modal dialogs for forms
- Conflict alerts with severity colors

---

#### `frontend/script.js` - Dashboard Logic
**Purpose**: Frontend JavaScript for dynamic behavior

**Key Functions**:

**Initialization**:
- `DOMContentLoaded`: Setup on page load
- `startAutoRefresh()`: 5-second auto-refresh
- `checkSystemHealth()`: Verify backend connection

**Data Loading**:
- `loadDashboard()`: Fetch all dashboard data
- `updateDashboardStats()`: Update stat cards
- `updateRunwaysList()`: Render runway cards
- `updateAircraftTable()`: Populate aircraft table
- `updateLandingQueue()`: Display queue items
- `updateConflicts()`: Show conflict alerts

**API Interactions**:
- `addToLandingQueue()`: POST to queue endpoint
- `processNextInQueue()`: Process next aircraft
- `removeFromQueue()`: Remove aircraft from queue
- `releaseRunway()`: Release occupied runway
- `addAircraft()`: Create new aircraft
- `addRunway()`: Create new runway

**UI Helpers**:
- `showAddAircraftModal()`: Display aircraft form
- `showAddRunwayModal()`: Display runway form
- `closeModal()`: Close modal dialogs
- `showSuccess()`: Success notification
- `showError()`: Error notification

**Constants**:
- `API_BASE_URL`: Backend API URL (http://localhost:5000/api)

---

### Configuration Files

#### `requirements.txt` - Python Dependencies
**Purpose**: List of Python packages required

**Dependencies**:
```
Flask==3.0.0                    # Web framework
Flask-CORS==4.0.0              # CORS support
Flask-SQLAlchemy==3.1.1        # ORM
psycopg2-binary==2.9.9         # PostgreSQL driver
python-dotenv==1.0.0           # Environment variables
gunicorn==21.2.0               # Production WSGI server
pytest==7.4.3                  # Testing framework
pytest-flask==1.3.0            # Flask testing utilities
```

---

#### `.env.example` - Environment Template
**Purpose**: Template for environment variables

**Variables**:
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Flask secret key
- `FLASK_ENV`: Environment (development/production)
- `PORT`: Server port (default 5000)

**Usage**:
```bash
copy .env.example .env
# Edit .env with your values
```

---

#### `.gitignore` - Git Ignore Rules
**Purpose**: Specify files to exclude from version control

**Ignored Items**:
- Python cache (`__pycache__/`, `*.pyc`)
- Virtual environments (`venv/`, `env/`)
- Environment files (`.env`)
- Database files (`*.db`, `*.sqlite3`)
- IDE files (`.vscode/`, `.idea/`)
- Build artifacts (`dist/`, `build/`)
- Log files (`*.log`)
- Frontend build files (`node_modules/`, `dist/`)

---

### Documentation Files

#### `README.md` - Main Documentation
**Sections**:
- Introduction and features
- Architecture overview
- Technology stack
- Installation instructions
- Usage guide
- API overview
- Testing guide
- Deployment options
- Safety considerations

---

#### `API_DOCUMENTATION.md` - API Reference
**Contents**:
- Complete endpoint reference
- Request/response examples
- Error codes and messages
- Constraint rules
- Status transition diagram
- Authentication (future)
- Rate limiting (future)

---

#### `QUICK_START.md` - Quick Start Guide
**Contents**:
- Prerequisites checklist
- Step-by-step installation
- Test scenarios
- Troubleshooting tips
- Common usage patterns
- Next steps and learning resources

---

## 🔄 Data Flow

### Request Flow Example: Add to Landing Queue

```
1. User clicks "Request Landing" button
   ↓
2. Frontend (script.js): addToLandingQueue(aircraftId)
   ↓
3. HTTP POST to /api/landing-queue
   ↓
4. Backend (app.py): add_to_landing_queue() endpoint
   ↓
5. Services (services.py): QueueService.add_to_landing_queue()
   ↓
6. Models (models.py): LandingQueue model, database insert
   ↓
7. Database: Insert record with priority
   ↓
8. Response: JSON with queue item details
   ↓
9. Frontend: Update dashboard, show success message
```

### Status Transition Flow

```
Parked → Taxiing → Takeoff → In-Air → Landing → Taxiing → Parked
```

Each transition validated by `ConstraintService.validate_aircraft_status_transition()`

### Conflict Detection Flow

```
Periodic Check (every dashboard refresh)
   ↓
GET /api/conflicts
   ↓
ConflictDetectionService.detect_all_conflicts()
   ↓
check_runway_conflicts() + check_landing_queue_conflicts()
   ↓
Return conflicts with severity
   ↓
Display in dashboard if any found
```

## 🎨 Design Patterns Used

1. **MVC Pattern**: Models (models.py), Controllers (app.py), Views (frontend/)
2. **Service Layer**: Business logic separated in services.py
3. **Factory Pattern**: Flask app factory in app.py
4. **ORM Pattern**: SQLAlchemy models abstract database
5. **RESTful API**: Standard HTTP methods and resource URLs

## 🔐 Security Considerations

### Current Implementation
- CORS enabled for development
- No authentication (suitable for internal/educational use)
- Input validation on models
- SQL injection prevention via ORM

### Production Recommendations
- Add JWT or OAuth2 authentication
- Implement rate limiting
- Use HTTPS
- Validate all inputs
- Add audit logging
- Use environment-specific secrets

## 🚀 Extension Points

### Easy to Add
1. **New Aircraft Types**: Extend AircraftSize enum
2. **Additional Constraints**: Add to ConstraintService
3. **New Conflict Types**: Add to ConflictDetectionService
4. **More Endpoints**: Add to app.py
5. **Dashboard Features**: Extend frontend files

### Suggested Enhancements
1. WebSocket support for real-time updates
2. Flight path tracking
3. Weather integration
4. Fuel management
5. Crew scheduling
6. Maintenance tracking
7. Historical data analytics
8. Multi-airport support

## 📊 Database Relationships

```
Aircraft 1───n Flight
Aircraft 1───n LandingQueue
Aircraft n───1 Runway (current_runway_id)
Aircraft n───1 Gate (current_gate_id)
Flight n───1 Runway (assigned_runway_id)
Flight n───1 Gate (assigned_gate_id)
LandingQueue n───1 Runway (assigned_runway_id)
```

---

**This structure provides a solid foundation for an automated Air Traffic Control system with clear separation of concerns and extensibility.**
