// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';
let refreshInterval;

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', () => {
    checkSystemHealth();
    loadDashboard();
    startAutoRefresh();
});

// Auto-refresh every 5 seconds
function startAutoRefresh() {
    refreshInterval = setInterval(() => {
        loadDashboard();
    }, 5000);
}

// Check system health
async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        const statusEl = document.getElementById('systemStatus');
        if (data.status === 'healthy') {
            statusEl.className = 'status-value healthy';
            statusEl.textContent = '●';
        } else {
            statusEl.className = 'status-value danger';
            statusEl.textContent = '●';
        }
    } catch (error) {
        console.error('Health check failed:', error);
        document.getElementById('systemStatus').className = 'status-value danger';
        document.getElementById('systemStatus').textContent = '●';
    }
}

// Load complete dashboard data
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard`);
        const data = await response.json();

        updateDashboardStats(data);
        updateRunwaysList(data.runways.list);
        updateAircraftTable(data.aircraft.list);
        updateLandingQueue(data.landing_queue.queue);
        updateConflicts(data.conflicts);

        // Update last update time
        const now = new Date();
        document.getElementById('lastUpdate').textContent = now.toLocaleTimeString();
    } catch (error) {
        console.error('Failed to load dashboard:', error);
        showError('Failed to load dashboard data');
    }
}

// Update dashboard statistics
function updateDashboardStats(data) {
    document.getElementById('totalAircraft').textContent = data.aircraft.total;
    document.getElementById('aircraftInAir').textContent = data.aircraft.in_air;
    document.getElementById('aircraftLanding').textContent = data.aircraft.landing;
    document.getElementById('aircraftParked').textContent = data.aircraft.parked;

    document.getElementById('totalRunways').textContent = data.runways.total;
    document.getElementById('runwaysAvailable').textContent = data.runways.available;
    document.getElementById('runwaysOccupied').textContent = data.runways.occupied;

    document.getElementById('queueCount').textContent = data.landing_queue.count;
}

// Update runways list
function updateRunwaysList(runways) {
    const container = document.getElementById('runwaysList');
    container.innerHTML = '';

    if (runways.length === 0) {
        container.innerHTML = '<p style="color: #64748b;">No runways configured. Add a runway to get started.</p>';
        return;
    }

    runways.forEach(runway => {
        const card = document.createElement('div');
        card.className = `runway-card ${runway.status.toLowerCase()}`;

        card.innerHTML = `
            <div class="runway-header">
                <div class="runway-name">${runway.name}</div>
                <span class="runway-status ${runway.status.toLowerCase()}">${runway.status}</span>
            </div>
            <div class="runway-details">
                <div><strong>Length:</strong> ${runway.length}m</div>
                <div><strong>Suitable for:</strong> ${getSuitableAircraftSizes(runway.length)}</div>
                ${runway.occupied_by ? `<div><strong>Occupied by:</strong> ${runway.occupied_by}</div>` : ''}
            </div>
            <div class="runway-actions">
                ${runway.status === 'Occupied' ?
                    `<button class="btn btn-success btn-small" onclick="releaseRunway(${runway.id})">Release</button>` :
                    '<button class="btn btn-primary btn-small" disabled>Available</button>'
                }
            </div>
        `;

        container.appendChild(card);
    });
}

// Get suitable aircraft sizes based on runway length
function getSuitableAircraftSizes(length) {
    const sizes = [];
    if (length >= 1500) sizes.push('Small');
    if (length >= 2500) sizes.push('Medium');
    if (length >= 3500) sizes.push('Heavy');
    return sizes.join(', ') || 'None';
}

// Update aircraft table
function updateAircraftTable(aircraft) {
    const tbody = document.getElementById('aircraftTableBody');
    tbody.innerHTML = '';

    if (aircraft.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: #64748b;">No aircraft registered.</td></tr>';
        return;
    }

    aircraft.forEach(plane => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${plane.id}</strong></td>
            <td>${plane.model}</td>
            <td>${plane.size}</td>
            <td><span class="status-badge ${plane.status.toLowerCase().replace('-', '')}">${plane.status}</span></td>
            <td>${plane.altitude}</td>
            <td>${plane.speed}</td>
            <td>${plane.current_runway_id || '-'}</td>
            <td>
                ${plane.status === 'In-Air' ?
                    `<button class="btn btn-warning btn-small" onclick="addToLandingQueue('${plane.id}')">Request Landing</button>` :
                    '<button class="btn btn-small" disabled>-</button>'
                }
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Update landing queue
function updateLandingQueue(queue) {
    const container = document.getElementById('landingQueueList');
    container.innerHTML = '';

    if (queue.length === 0) {
        container.innerHTML = '<p style="color: #64748b;">No aircraft in landing queue.</p>';
        return;
    }

    queue.forEach((item, index) => {
        const queueItem = document.createElement('div');
        queueItem.className = 'queue-item';

        queueItem.innerHTML = `
            <div class="queue-item-priority">${item.priority}</div>
            <div class="queue-item-details">
                <strong>Aircraft ${item.aircraft_id}</strong><br>
                <small>Requested: ${new Date(item.requested_at).toLocaleTimeString()}</small>
                ${item.assigned_runway_id ? `<br><small style="color: #10b981;">✓ Assigned to Runway ${item.assigned_runway_id}</small>` : ''}
            </div>
            <button class="btn btn-danger btn-small" onclick="removeFromQueue('${item.aircraft_id}')">Remove</button>
        `;

        container.appendChild(queueItem);
    });
}

// Update conflicts display
function updateConflicts(conflicts) {
    const section = document.getElementById('conflictsSection');
    const container = document.getElementById('conflictsList');
    const countEl = document.getElementById('conflictCount');

    countEl.textContent = conflicts.count;

    if (conflicts.count === 0) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    container.innerHTML = '';

    conflicts.list.forEach(conflict => {
        const item = document.createElement('div');
        item.className = `conflict-item ${conflict.severity.toLowerCase()}`;

        item.innerHTML = `
            <strong>${conflict.severity}:</strong> ${conflict.message || getConflictMessage(conflict)}
        `;

        container.appendChild(item);
    });
}

// Get conflict message
function getConflictMessage(conflict) {
    if (conflict.type === 'runway_multi_assign') {
        return `Runway ${conflict.runway} has multiple aircraft assigned: ${conflict.aircraft.join(', ')}`;
    }
    return conflict.type;
}

// Add aircraft to landing queue
async function addToLandingQueue(aircraftId) {
    try {
        const response = await fetch(`${API_BASE_URL}/landing-queue`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({aircraft_id: aircraftId})
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess(data.message);
            loadDashboard();
        } else {
            showError(data.error || 'Failed to add to landing queue');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to add aircraft to landing queue');
    }
}

// Process next in queue
async function processNextInQueue() {
    try {
        const response = await fetch(`${API_BASE_URL}/landing-queue/process-next`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess(data.message);
            loadDashboard();
        } else {
            showError(data.error || 'Failed to process queue');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to process landing queue');
    }
}

// Remove from queue
async function removeFromQueue(aircraftId) {
    try {
        const response = await fetch(`${API_BASE_URL}/landing-queue/${aircraftId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess(data.message);
            loadDashboard();
        } else {
            showError(data.error || 'Failed to remove from queue');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to remove from queue');
    }
}

// Release runway
async function releaseRunway(runwayId) {
    try {
        const response = await fetch(`${API_BASE_URL}/runways/${runwayId}/release`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess(data.message);
            loadDashboard();
        } else {
            showError(data.error || 'Failed to release runway');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to release runway');
    }
}

// Add new aircraft
async function addAircraft(event) {
    event.preventDefault();

    const aircraftData = {
        id: document.getElementById('aircraftId').value,
        model: document.getElementById('aircraftModel').value,
        size: document.getElementById('aircraftSize').value,
        status: document.getElementById('aircraftStatus').value
    };

    try {
        const response = await fetch(`${API_BASE_URL}/aircraft`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(aircraftData)
        });

        if (response.ok) {
            showSuccess('Aircraft added successfully');
            closeModal('addAircraftModal');
            document.getElementById('addAircraftForm').reset();
            loadDashboard();
        } else {
            const data = await response.json();
            showError(data.error || 'Failed to add aircraft');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to add aircraft');
    }
}

// Add new runway
async function addRunway(event) {
    event.preventDefault();

    const runwayData = {
        name: document.getElementById('runwayName').value,
        length: parseInt(document.getElementById('runwayLength').value)
    };

    try {
        const response = await fetch(`${API_BASE_URL}/runways`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(runwayData)
        });

        if (response.ok) {
            showSuccess('Runway added successfully');
            closeModal('addRunwayModal');
            document.getElementById('addRunwayForm').reset();
            loadDashboard();
        } else {
            const data = await response.json();
            showError(data.error || 'Failed to add runway');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to add runway');
    }
}

// Modal functions
function showAddAircraftModal() {
    document.getElementById('addAircraftModal').style.display = 'block';
}

function showAddRunwayModal() {
    document.getElementById('addRunwayModal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.className === 'modal') {
        event.target.style.display = 'none';
    }
}

// Notification functions
function showSuccess(message) {
    alert('✓ ' + message);
}

function showError(message) {
    alert('✗ ' + message);
}
