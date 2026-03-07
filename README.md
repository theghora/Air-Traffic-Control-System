# 🛫 Air Traffic Control System

An automated, distributed Air Traffic Control (ATC) System built with modern cloud computing principles to handle real-time aircraft monitoring, runway management, and flight operations with high availability and fault tolerance.

## 📋 Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

## 🎯 Introduction

Managing air traffic is a complex task that requires real-time monitoring of aircraft on the ground and in the air. Traditional manual systems can be prone to human error and scaling issues. This automated ATC system provides:

- **Real-time monitoring** of aircraft positions and status
- **Automated constraint validation** for runway assignments
- **Conflict detection** to prevent safety violations
- **FIFO queue management** for landing operations
- **High availability** through distributed architecture

## ✨ Features

### Core Features

1. **Aircraft Management**
   - Track aircraft by ID, model, size (Small/Medium/Heavy), and status
   - Real-time status updates (In-Air, Landing, Taxiing, Parked, Takeoff)
   - Altitude and speed monitoring

2. **Runway Management**
   - Multiple runway support with length specifications
   - Automated suitability checks based on aircraft size
   - Runway cooldown period enforcement
   - Real-time availability status

3. **Constraint Logic**
   - **Runway Length Requirements:**
     - Small aircraft: 1,500m minimum
     - Medium aircraft: 2,500m minimum
     - Heavy aircraft: 3,500m minimum
   - **Occupancy Rules:** One aircraft per runway at a time
   - **Cooldown Period:** 60-second minimum between uses
   - **Status Transitions:** Validated state machine for aircraft movements

4. **Conflict Detection**
   - Automatic detection of runway multi-assignments
   - Landing queue validation
   - Real-time conflict alerts with severity levels (Critical, High, Medium)

5. **Landing Queue (FIFO)**
   - First-In-First-Out queue management
   - Automatic runway assignment to next aircraft
   - Priority-based processing

6. **Controller Dashboard**
   - Live status monitor for all aircraft and runways
   - Real-time statistics and metrics
   - Conflict alerts and warnings
   - Management controls for aircraft and runway operations

## 🏗 Architecture

The system follows a distributed, client-server architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Dashboard)                  │
│              HTML5 + CSS3 + Vanilla JavaScript          │
└────────────────────┬────────────────────────────────────┘
                     │ REST API
                     │
┌────────────────────┴────────────────────────────────────┐
│                   Backend API Server                     │
│                  Flask + SQLAlchemy                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Constraint  │  │   Conflict   │  │    Queue     │ │
│  │   Service    │  │  Detection   │  │   Service    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              Database (PostgreSQL / SQLite)              │
│   Aircraft | Runways | Flights | Queue | Gates | ...    │
└─────────────────────────────────────────────────────────┘
```

### Key Components

1. **Models Layer** (`models.py`): Database schema and ORM models
2. **Services Layer** (`services.py`): Business logic for constraints, conflicts, and queues
3. **API Layer** (`app.py`): REST API endpoints
4. **Frontend Layer** (`frontend/`): Controller dashboard interface

## 🛠 Technology Stack

### Backend
- **Python 3.8+**: Core programming language
- **Flask**: Web framework for REST API
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL/SQLite**: Database engines

### Frontend
- **HTML5/CSS3**: Structure and styling
- **Vanilla JavaScript**: Dynamic interactions and API calls
- **Responsive Design**: Mobile and desktop compatible

### Development
- **pytest**: Unit and integration testing
- **Flask-CORS**: Cross-origin resource sharing
- **python-dotenv**: Environment configuration

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- PostgreSQL (optional, SQLite used by default)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd Air-Traffic-Control-System
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy example environment file
copy .env.example .env

# Edit .env with your settings (optional)
# By default, uses SQLite database
```

### Step 5: Initialize Database

```bash
python init_db.py
```

This creates sample data including:
- 4 runways
- 10 gates
- 5 taxiways
- 6 aircraft
- 3 flights

### Step 6: Start the Server

```bash
python app.py
```

The API server will start at `http://localhost:5000`

### Step 7: Open Dashboard

Open `frontend/index.html` in your web browser or serve it with:

```bash
# Using Python's built-in server
cd frontend
python -m http.server 8080
```

Then navigate to `http://localhost:8080`

---

## 🪟 Windows Quick Start

For Windows users, here's a streamlined setup process:

### PowerShell Commands (Copy & Paste)

```powershell
# 1. Navigate to project directory
cd C:\Users\tahag\Desktop\Projects\Air-Traffic-Control-System

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database with sample data
python init_db.py

# 5. Start backend server
python app.py
```

Keep the PowerShell window open, then:

**Option A:** Double-click `frontend\index.html` in File Explorer

**Option B:** Open new PowerShell window and run:
```powershell
cd C:\Users\tahag\Desktop\Projects\Air-Traffic-Control-System\frontend
python -m http.server 8080
```
Navigate to: http://localhost:8080

### Common Windows Issues

**Script execution disabled?**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Port 5000 in use?**
```powershell
# Find and kill process
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Python not found?**
```powershell
# Use Python Launcher
py -m venv venv
py app.py
```

---

## 🚀 Usage

### Controller Dashboard

The dashboard provides real-time monitoring and control:

1. **Overview Cards**: Quick stats on aircraft, runways, and queue
2. **Runway Status**: Visual representation of all runways and their availability
3. **Aircraft Table**: Complete list of all aircraft with current status
4. **Landing Queue**: FIFO queue for landing requests
5. **Conflict Alerts**: Real-time warnings for safety violations

### Common Operations

#### Add Aircraft to Landing Queue
1. Aircraft must be "In-Air" status
2. Click "Request Landing" button next to aircraft
3. Aircraft added to queue with FIFO priority

#### Process Landing Queue
1. Click "Process Next" button in Landing Queue section
2. System automatically:
   - Selects next aircraft in queue
   - Finds suitable available runway
   - Assigns runway to aircraft
   - Updates statuses

#### Release Runway
1. When aircraft completes runway usage
2. Click "Release" button on runway card
3. Runway becomes available for next aircraft

#### Add New Aircraft
1. Click "+ Add Aircraft" button
2. Fill in aircraft details (ID, model, size, status)
3. Submit form

#### Add New Runway
1. Click "+ Add Runway" button
2. Specify runway name and length
3. Submit form

## 📚 API Documentation

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.

### Base URL
```
http://localhost:5000/api
```

### Key Endpoints

- `GET /api/dashboard` - Get complete dashboard data
- `GET /api/aircraft` - List all aircraft
- `POST /api/aircraft` - Create new aircraft
- `GET /api/runways` - List all runways
- `POST /api/runways/{id}/assign` - Assign runway to aircraft
- `POST /api/runways/{id}/release` - Release runway
- `GET /api/landing-queue` - Get landing queue
- `POST /api/landing-queue/process-next` - Process next in queue
- `GET /api/conflicts` - Detect conflicts

## 🧪 Testing

The project includes comprehensive unit and integration tests.

### Run All Tests

```bash
pytest test_atc.py -v
```

### Run Specific Test

```bash
pytest test_atc.py::test_runway_length_constraint -v
```

### Test Coverage

The test suite covers:
- ✅ Runway length constraints
- ✅ Runway occupancy validation
- ✅ Aircraft status transitions
- ✅ FIFO queue ordering
- ✅ Conflict detection
- ✅ API endpoints

## 🌐 Deployment

### Local Deployment

1. Follow installation instructions above
2. Configure `.env` for production settings
3. Use PostgreSQL for production database
4. Run with production WSGI server:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Cloud Deployment (AWS Example)

1. **Database**: AWS RDS PostgreSQL
2. **Backend**: AWS Lambda + API Gateway (serverless) or EC2
3. **Frontend**: AWS S3 + CloudFront
4. **Monitoring**: CloudWatch

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:

```bash
docker build -t atc-system .
docker run -p 5000:5000 atc-system
```

## 🔒 Safety Considerations

This system implements multiple safety constraints:

1. **Runway Length Validation**: Prevents aircraft from using unsuitable runways
2. **Occupancy Control**: Ensures only one aircraft per runway
3. **Cooldown Enforcement**: Prevents immediate reuse of runways
4. **Status Validation**: Ensures valid state transitions
5. **Conflict Detection**: Real-time monitoring for violations
6. **FIFO Queue**: Fair and predictable landing order

## 🎓 Educational Purpose

This project demonstrates:
- Distributed system design
- Real-time data management
- Constraint satisfaction problems
- REST API architecture
- Database modeling
- Frontend-backend integration
- Safety-critical system design

## 📝 License

This project is created for educational purposes as part of a course project (COE892).

## 🤝 Contributing

This is a course project. For suggestions or improvements:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Contact

For questions or support regarding this project, please contact the development team.

---

**Built with ❤️ for safe and efficient air traffic management**