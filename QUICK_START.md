# Quick Start Guide - ATC System

## 🚀 Get Started in 5 Minutes

This guide will get your ATC system up and running quickly.

## Prerequisites Check

Before you begin, ensure you have:
- ✅ Python 3.8 or higher installed
- ✅ pip package manager
- ✅ A web browser (Chrome, Firefox, Edge, etc.)

Check your Python version:
```bash
python --version
```

## Installation Steps

### 1. Navigate to Project Directory

```bash
cd Air-Traffic-Control-System
```

### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- SQLAlchemy (database ORM)
- Flask-CORS (API cross-origin support)
- pytest (testing framework)

### 4. Initialize Database with Sample Data

```bash
python init_db.py
```

Expected output:
```
Creating database tables...
Adding runways...
Adding gates...
Adding taxiways...
Adding aircraft...
Adding flights...

✓ Database initialized successfully!
  - 4 runways
  - 10 gates
  - 5 taxiways
  - 6 aircraft
  - 3 flights

You can now start the application with: python app.py
```

### 5. Start the Backend Server

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

**Keep this terminal window open!**

### 6. Open the Dashboard

**Option A: Direct File Open**
1. Navigate to the `frontend` folder
2. Double-click `index.html`
3. It will open in your default browser

**Option B: Using Python HTTP Server** (Recommended)

Open a **new terminal window**:

```bash
cd frontend
python -m http.server 8080
```

Then open your browser to: `http://localhost:8080`

## 🎮 Try It Out!

### Test Scenario 1: View System Status

1. Dashboard should load showing:
   - 6 aircraft total
   - 2 aircraft in air (AC004, AC005)
   - 4 runways available
   - Empty landing queue

### Test Scenario 2: Request Landing

1. Find aircraft `AC004` (Boeing 777) in the aircraft table
2. Click "Request Landing" button
3. Aircraft appears in Landing Queue with priority 1
4. Click "Process Next" button in Landing Queue section
5. Watch as:
   - System finds suitable runway
   - Runway assigned to aircraft
   - Runway status changes to "Occupied"

### Test Scenario 3: Add New Aircraft

1. Click "+ Add Aircraft" button
2. Fill in:
   - ID: `AC007`
   - Model: `Boeing 787`
   - Size: `Heavy`
   - Status: `Parked`
3. Click "Add Aircraft"
4. New aircraft appears in the table

### Test Scenario 4: Release Runway

1. Find an occupied runway (e.g., after Test Scenario 2)
2. Click "Release" button
3. Runway becomes available again

## 🔍 Verify Installation

### Test the API Directly

Open a new terminal and test with curl or your browser:

```bash
# Health check
curl http://localhost:5000/api/health

# Get all aircraft
curl http://localhost:5000/api/aircraft

# Get dashboard data
curl http://localhost:5000/api/dashboard
```

Or visit in browser:
- http://localhost:5000/api/health
- http://localhost:5000/api/dashboard

### Run Tests

```bash
pytest test_atc.py -v
```

All tests should pass:
```
test_atc.py::test_health_endpoint PASSED
test_atc.py::test_create_aircraft PASSED
test_atc.py::test_runway_length_constraint PASSED
test_atc.py::test_runway_occupied_constraint PASSED
test_atc.py::test_landing_queue_fifo PASSED
test_atc.py::test_conflict_detection_runway PASSED
```

## 📊 Understanding the Dashboard

### Top Status Bar
- **System Status**: Green dot = healthy
- **Critical Conflicts**: Shows count of safety violations
- **Last Update**: Auto-refreshes every 5 seconds

### Overview Cards
- **Aircraft Card**: Total count and breakdown by status
- **Runways Card**: Available vs. occupied runways
- **Landing Queue Card**: Number of aircraft waiting

### Runways Section
- Each runway shows:
  - Name and length
  - Status (Available/Occupied)
  - Suitable aircraft sizes
  - Release button (if occupied)

### Aircraft Table
- Complete list with:
  - ID, Model, Size, Status
  - Current altitude and speed
  - Assigned runway
  - Action buttons

### Landing Queue
- Shows aircraft in order (FIFO)
- Priority number (1 = first)
- Request timestamp
- Assigned runway (if any)

## ⚠️ Troubleshooting

### Port Already in Use

If you see "Address already in use":

**Windows:**
```powershell
# Find process on port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

**macOS/Linux:**
```bash
# Find and kill process on port 5000
lsof -ti:5000 | xargs kill -9
```

### CORS Errors in Browser

Make sure:
1. Backend server is running on port 5000
2. Frontend is served (not just file:/// protocol)
3. Check browser console for specific error

### Database Locked Error

If using SQLite and you see "database is locked":
1. Close all Python processes
2. Delete `atc_system.db` file
3. Run `python init_db.py` again

### Module Not Found

```bash
# Make sure virtual environment is activated
# Windows:
.\venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## 🎯 Next Steps

Now that your system is running:

1. **Read the Full Documentation**: Check [README.md](README.md) for detailed features
2. **Explore the API**: See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for endpoint details
3. **Run Tests**: Execute `pytest` to understand the test suite
4. **Experiment**: Try different scenarios with aircraft and runways
5. **Modify**: Edit code and see changes in real-time

## 📚 Learning Resources

### Understanding the Code

- **models.py**: Database schema - start here to understand data structure
- **services.py**: Business logic - constraint validation and conflict detection
- **app.py**: REST API endpoints - how frontend communicates with backend
- **frontend/script.js**: Dashboard logic - how UI updates

### Key Concepts

1. **Constraint Satisfaction**: How runway assignments are validated
2. **FIFO Queue**: Landing queue implements First-In-First-Out
3. **Conflict Detection**: Real-time safety violation monitoring
4. **REST API**: Stateless communication between client and server

## 💡 Common Usage Patterns

### Simulating Aircraft Landing

1. Create aircraft with "In-Air" status
2. Add to landing queue
3. Process queue to assign runway
4. Update status to "Landing"
5. Update status to "Taxiing"
6. Release runway
7. Update status to "Parked"

### Testing Constraints

Try these scenarios to see constraint validation:

1. **Runway Too Short**:
   - Create Heavy aircraft
   - Try to assign 2000m runway
   - Should fail with error

2. **Runway Occupied**:
   - Assign runway to aircraft A
   - Try to assign same runway to aircraft B
   - Should fail with error

3. **Invalid Status Transition**:
   - Try to change Parked → In-Air directly
   - Should fail (must go through Taxiing → Takeoff first)

## 🆘 Getting Help

If you encounter issues:

1. Check the terminal output for error messages
2. Check browser console (F12) for frontend errors
3. Review the troubleshooting section above
4. Check the full README.md for more details
5. Run tests to verify system integrity

---

**Happy Testing! 🛫**
