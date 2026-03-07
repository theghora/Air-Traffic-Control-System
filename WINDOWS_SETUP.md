# 🪟 Windows Setup Guide - Air Traffic Control System

Complete step-by-step guide for setting up the ATC System on Windows 10/11.

---

## 📋 Prerequisites

### Required Software

1. **Python 3.8 or higher**
   - Download from: https://www.python.org/downloads/
   - ✅ During installation: Check "Add Python to PATH"
   - ✅ Check "Install pip"

2. **Web Browser**
   - Chrome, Edge, Firefox, or any modern browser

3. **Text Editor** (Optional)
   - VS Code, Notepad++, or any text editor

### Check Python Installation

Open PowerShell (Win + X → PowerShell) and run:

```powershell
python --version
```

Should show: `Python 3.8.x` or higher

```powershell
pip --version
```

Should show: `pip 20.x.x` or higher

---

## 🚀 Installation Steps

### Step 1: Open PowerShell

**Method 1:** Press `Win + X`, select "Windows PowerShell" or "Terminal"

**Method 2:** Press `Win + R`, type `powershell`, press Enter

**Method 3:** Search for "PowerShell" in Start Menu

### Step 2: Navigate to Project

```powershell
cd C:\Users\tahag\Desktop\Projects\Air-Traffic-Control-System
```

💡 **Tip:** You can type `cd` then drag the folder from File Explorer into PowerShell

Verify you're in the right directory:
```powershell
ls
```

You should see: `README.md`, `app.py`, `requirements.txt`, etc.

### Step 3: Create Virtual Environment

```powershell
python -m venv venv
```

This creates a `venv` folder (takes 10-15 seconds)

### Step 4: Activate Virtual Environment

```powershell
.\venv\Scripts\activate
```

✅ Your prompt should change to: `(venv) PS C:\Users\tahag\Desktop\Projects\Air-Traffic-Control-System>`

#### 🔧 Troubleshooting: Script Execution Error

If you see: `cannot be loaded because running scripts is disabled`

**Solution:**
```powershell
# Run PowerShell as Administrator
# Then execute:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Type 'Y' and press Enter
# Close admin PowerShell and try activating again in your regular PowerShell:
.\venv\Scripts\activate
```

### Step 5: Install Dependencies

```powershell
pip install -r requirements.txt
```

This installs all required packages (~30-60 seconds):
- Flask (web framework)
- SQLAlchemy (database)
- Flask-CORS (cross-origin requests)
- pytest (testing)
- and others...

You'll see a progress bar for each package.

### Step 6: Initialize Database

```powershell
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

✅ A file `atc_system.db` is created in your project folder

### Step 7: Start Backend Server

```powershell
python app.py
```

You should see:
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

✅ Backend is running!

⚠️ **Important:** Keep this PowerShell window open!

### Step 8: Open Frontend Dashboard

You have two options:

#### **Option A: Simple File Open** (Easiest)

1. Open File Explorer (`Win + E`)
2. Navigate to: `C:\Users\tahag\Desktop\Projects\Air-Traffic-Control-System\frontend`
3. Double-click `index.html`
4. Your default browser opens with the dashboard

✅ Dashboard should load and show aircraft/runways

#### **Option B: Python HTTP Server** (Recommended)

1. Open a **NEW** PowerShell window
2. Keep the first PowerShell (backend) running!

In the new window:
```powershell
# Navigate to project
cd C:\Users\tahag\Desktop\Projects\Air-Traffic-Control-System

# Activate virtual environment
.\venv\Scripts\activate

# Go to frontend folder
cd frontend

# Start HTTP server
python -m http.server 8080
```

Output:
```
Serving HTTP on :: port 8080 (http://[::]:8080/) ...
```

3. Open your browser
4. Go to: **http://localhost:8080**

✅ Dashboard loads with better compatibility

---

## 🎮 Using the System

### First Look

When dashboard loads, you should see:

**Top Status Bar:**
- 🟢 System Status: Healthy
- 0 Critical Conflicts
- Last Update: (current time)

**Overview Cards:**
- Aircraft: 6 total (2 in air, 4 parked/taxiing)
- Runways: 4 total (all available initially)
- Landing Queue: 0 aircraft

**Main Sections:**
- Runways Status (4 runway cards)
- Aircraft Status (table with 6 aircraft)
- Landing Queue (empty initially)

### Try It Out!

#### Test 1: Request Landing

1. Find aircraft **AC004** (Boeing 777, In-Air) in the table
2. Click the **"Request Landing"** button
3. ✅ Aircraft appears in Landing Queue with Priority 1
4. Click **"Process Next"** in Landing Queue section
5. ✅ System assigns suitable runway
6. ✅ Runway card shows "Occupied by AC004"

#### Test 2: Add New Aircraft

1. Click **"+ Add Aircraft"** button at top
2. Fill in the form:
   - **ID:** AC007
   - **Model:** Boeing 787 Dreamliner
   - **Size:** Heavy
   - **Status:** Parked
3. Click **"Add Aircraft"**
4. ✅ New aircraft appears in table

#### Test 3: Release Runway

1. Find a runway with "Occupied" status
2. Click the **"Release"** button
3. ✅ Runway status changes to "Available"

#### Test 4: Test Constraints

1. Try to add aircraft **AC002** (Airbus A380, Heavy) to landing queue
2. Click "Process Next"
3. If only short runways available (< 3500m):
   - ❌ System shows error: "No suitable runway available"
   - ✅ Constraint working correctly!

---

## 🧪 Testing

### Run Automated Tests

In PowerShell with venv activated:

```powershell
pytest test_atc.py -v
```

Expected output:
```
test_atc.py::test_health_endpoint PASSED                    [ 16%]
test_atc.py::test_create_aircraft PASSED                    [ 33%]
test_atc.py::test_runway_length_constraint PASSED           [ 50%]
test_atc.py::test_runway_occupied_constraint PASSED         [ 66%]
test_atc.py::test_landing_queue_fifo PASSED                 [ 83%]
test_atc.py::test_conflict_detection_runway PASSED          [100%]

======================== 6 passed in 2.45s =========================
```

✅ All tests should pass!

---

## 🔧 Troubleshooting

### Issue 1: "python is not recognized"

**Cause:** Python not in PATH

**Solution 1:** Use Python Launcher
```powershell
py --version
py -m venv venv
py app.py
```

**Solution 2:** Add Python to PATH
1. Search for "Environment Variables" in Start Menu
2. Click "Edit the system environment variables"
3. Click "Environment Variables" button
4. Under "System variables", find "Path"
5. Click "Edit" → "New"
6. Add: `C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python3XX`
7. Add: `C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python3XX\Scripts`
8. Click OK, restart PowerShell

### Issue 2: Can't activate virtual environment

**Error:** `Scripts\activate : cannot be loaded because running scripts is disabled`

**Solution:**
```powershell
# Run PowerShell as Administrator (Right-click → Run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Type Y and press Enter
# Close admin PowerShell, open regular PowerShell
.\venv\Scripts\activate
```

### Issue 3: Port 5000 already in use

**Error:** `OSError: [Errno 98] Address already in use`

**Solution 1:** Find and kill the process
```powershell
# Find process on port 5000
netstat -ano | findstr :5000

# Output shows: TCP  0.0.0.0:5000  LISTENING  12345
# The number at the end (12345) is the Process ID (PID)

# Kill the process (replace 12345 with actual PID)
taskkill /PID 12345 /F
```

**Solution 2:** Use a different port
```powershell
$env:PORT = 5001
python app.py
```

Then update `frontend/script.js`:
```javascript
const API_BASE_URL = 'http://localhost:5001/api';
```

### Issue 4: Dashboard shows "Failed to connect"

**Checklist:**
1. ✅ Backend running? Check PowerShell window
2. ✅ Visit http://localhost:5000/api/health - should show `{"status":"healthy"}`
3. ✅ Check browser console (F12) for errors
4. ✅ CORS issue? Ensure backend has Flask-CORS installed
5. ✅ Firewall blocking? Temporarily disable and test

**Solution:** Check API URL in `frontend/script.js`:
```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

### Issue 5: Database locked

**Error:** `sqlite3.OperationalError: database is locked`

**Solution:**
```powershell
# Close all Python processes
taskkill /F /IM python.exe

# Delete database file
Remove-Item atc_system.db

# Reinitialize
python init_db.py
python app.py
```

### Issue 6: Import errors

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Cause:** Virtual environment not activated or dependencies not installed

**Solution:**
```powershell
# Activate venv
.\venv\Scripts\activate

# Verify activation - you should see (venv) in prompt

# Reinstall dependencies
pip install -r requirements.txt

# Verify Flask installed
pip list | findstr Flask
```

### Issue 7: Frontend looks broken

**Possible causes:**
- CSS not loading
- JavaScript not running
- Wrong files opened

**Solution:**
1. Clear browser cache (Ctrl + Shift + Delete)
2. Hard refresh (Ctrl + F5)
3. Open browser console (F12) and check for errors
4. Ensure you're opening `frontend/index.html`, not `index.html` from root
5. Try different browser

---

## 📂 File Structure

```
Air-Traffic-Control-System/
│
├── venv/                       # Virtual environment (created by you)
│   └── Scripts/
│       └── activate           # Activation script
│
├── frontend/
│   ├── index.html            # Dashboard HTML
│   ├── styles.css            # Dashboard CSS
│   └── script.js             # Dashboard JavaScript
│
├── app.py                    # Backend API server
├── models.py                 # Database models
├── services.py               # Business logic
├── config.py                 # Configuration
├── init_db.py                # Database initialization
├── test_atc.py              # Test suite
│
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── atc_system.db            # SQLite database (created by init_db.py)
│
└── README.md                # Main documentation
```

---

## 🎯 Daily Usage

### Starting the System

**Terminal 1 (Backend):**
```powershell
cd C:\Users\tahag\Desktop\Projects\Air-Traffic-Control-System
.\venv\Scripts\activate
python app.py
```

**Terminal 2 (Frontend) - Optional:**
```powershell
cd C:\Users\tahag\Desktop\Projects\Air-Traffic-Control-System\frontend
python -m http.server 8080
```

**Or:** Just double-click `frontend\index.html`

### Stopping the System

- Press `Ctrl + C` in each PowerShell window
- Or close the PowerShell windows
- Frontend closes when you close browser tab

### Restarting

If anything goes wrong:
```powershell
# Stop everything (Ctrl + C in terminals)

# Restart backend
python app.py

# Dashboard auto-reconnects
```

### Resetting Database

To start fresh:
```powershell
.\venv\Scripts\activate
python init_db.py
```

This resets all aircraft, runways, and data back to initial state.

---

## 🎓 Learning Path

### Week 1: Getting Familiar
1. ✅ Complete setup (above)
2. ✅ Run tests: `pytest test_atc.py -v`
3. ✅ Explore dashboard features
4. ✅ Read [FEATURES_OVERVIEW.md](FEATURES_OVERVIEW.md)

### Week 2: Understanding Code
1. ✅ Open `models.py` - Understand database structure
2. ✅ Open `services.py` - See constraint logic
3. ✅ Open `app.py` - Explore API endpoints
4. ✅ Read [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

### Week 3: Testing Features
1. ✅ Test all constraint violations
2. ✅ Try to create conflicts intentionally
3. ✅ Monitor conflict detection
4. ✅ Read [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

### Week 4: Advanced Topics
1. ✅ Modify code (add new features)
2. ✅ Write new tests
3. ✅ Deploy to cloud (AWS guide)
4. ✅ Document changes

---

## 💡 Pro Tips

### PowerShell Tips

**Tab completion:** Type `cd Air` then press Tab - it auto-completes!

**Command history:** Press ↑ to see previous commands

**Clear screen:** Type `cls` or press `Ctrl + L`

**Copy/Paste in PowerShell:**
- Copy: Select text with mouse, right-click
- Paste: Right-click

### Development Tips

**Keep two terminals open:**
- Terminal 1: Backend (python app.py)
- Terminal 2: For commands (tests, init_db, etc.)

**Bookmark in browser:**
- http://localhost:5000/api/health (Backend health)
- http://localhost:8080 (Frontend dashboard)

**Use VS Code:** Install "Python" and "SQLite Viewer" extensions

### Testing Tips

**Quick health check:**
```powershell
curl http://localhost:5000/api/health
```

**View all aircraft:**
```powershell
curl http://localhost:5000/api/aircraft
```

**View dashboard data:**
```powershell
curl http://localhost:5000/api/dashboard
```

---

## 🆘 Getting Help

### Documentation Files

- **README.md** - Complete project overview
- **QUICK_START.md** - 5-minute setup guide
- **FEATURES_OVERVIEW.md** - Feature details (with Windows section!)
- **API_DOCUMENTATION.md** - API reference
- **PROJECT_STRUCTURE.md** - Code architecture
- **AWS_DEPLOYMENT.md** - Cloud deployment

### Debugging

**Backend issues:** Check PowerShell terminal output

**Frontend issues:** Press F12 in browser → Console tab

**Database issues:** Delete `atc_system.db` and run `python init_db.py`

**Connection issues:** Check http://localhost:5000/api/health

### Common Questions

**Q: Do I need PostgreSQL?**
A: No! System uses SQLite by default (included with Python)

**Q: Can I use Command Prompt instead of PowerShell?**
A: Yes, but PowerShell is recommended. Replace `.\venv\Scripts\activate` with `venv\Scripts\activate.bat`

**Q: Does this work on Windows 11?**
A: Yes! Same steps work on Windows 10 and 11

**Q: Can I change the port?**
A: Yes! Set `$env:PORT = 5001` before running `python app.py`

---

## ✅ Verification Checklist

Before considering setup complete, verify:

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (no errors)
- [ ] Database initialized (6 aircraft, 4 runways)
- [ ] Backend running (http://localhost:5000/api/health shows "healthy")
- [ ] Frontend loading (dashboard visible in browser)
- [ ] Can request landing for aircraft
- [ ] Can process landing queue
- [ ] All tests passing (pytest)

If all checked ✅ - You're ready to go! 🎉

---

**Need more help? Check the other documentation files or review this guide step by step.**

**Happy Air Traffic Controlling! 🛫✈️🛬**
