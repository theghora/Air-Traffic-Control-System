// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';
let refreshInterval;

// State for landing-time and takeoff-time modal
let pendingLandingAircraftId = null;
let pendingTakeoffAircraftId = null;

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
        const statusEl = document.getElementById('systemStatus');
        statusEl.className = 'status-value danger';
        statusEl.textContent = '●';
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
        renderLandingQueue(data.landing_queue.queue);
        renderTakeoffQueue(data.takeoff_queue?.queue || []);
        updateConflicts(data.conflicts);

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
    document.getElementById('takeoffQueueCount').textContent = data.takeoff_queue.count;
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
                ${
                    runway.status === 'Occupied'
                        ? '<button class="btn btn-secondary btn-small" disabled>Occupied</button>'
                        : '<button class="btn btn-primary btn-small" disabled>Available</button>'
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
        const actionButtons = getAircraftActionButtons(plane);

        row.innerHTML = `
            <td><strong>${plane.id}</strong></td>
            <td>${plane.model}</td>
            <td>${plane.size}</td>
            <td><span class="status-badge ${plane.status.toLowerCase().replaceAll('-', '')}">${plane.status}</span></td>
            <td>${plane.altitude}</td>
            <td>${plane.speed}</td>
            <td>${plane.current_runway_id || '-'}</td>
            <td>${actionButtons || '<button class="btn btn-small" disabled>-</button>'}</td>
        `;

        tbody.appendChild(row);
    });
}

// Action buttons for each aircraft row
function getAircraftActionButtons(aircraft) {
    let buttons = '';

    if (aircraft.status === 'In-Air') {
        buttons += `
            <button class="btn btn-warning btn-small" onclick="openLandingModal('${aircraft.id}')">
                Request Landing
            </button>
        `;
    }

    if (aircraft.status === 'Parked') {
        buttons += `
            <button class="btn btn-primary btn-small" onclick="requestTakeoff('${aircraft.id}')">
                Request Takeoff
            </button>
        `;
    }

    return buttons.trim();
}

// Landing modal functions
function openLandingModal(aircraftId) {
    pendingLandingAircraftId = aircraftId;

    const now = new Date();
    now.setSeconds(0, 0);
    const localISO = new Date(now - now.getTimezoneOffset() * 60000)
        .toISOString()
        .slice(0, 16);

    const timeInput = document.getElementById('landingTimeInput');
    const label = document.getElementById('landingModalAircraftLabel');
    const modal = document.getElementById('landingTimeModal');

    if (!timeInput || !label || !modal) {
        showError('Landing modal HTML is missing from index.html');
        return;
    }

    timeInput.value = localISO;
    label.textContent = `Aircraft: ${aircraftId}`;
    modal.style.display = 'flex';
}

function closeLandingModal() {
    const modal = document.getElementById('landingTimeModal');
    if (modal) {
        modal.style.display = 'none';
    }
    pendingLandingAircraftId = null;
}

async function confirmLandingRequest() {
    const aircraftId = pendingLandingAircraftId;
    if (!aircraftId) {
        showError('No aircraft selected for landing request');
        return;
    }

    const rawTime = document.getElementById('landingTimeInput')?.value;
    const body = { aircraft_id: aircraftId };

    if (rawTime) {
        body.scheduled_landing_time = `${rawTime}:00`;
    }
    try {
        const response = await fetch(`${API_BASE_URL}/landing-queue`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        if (response.ok) {
            closeLandingModal();
            showSuccess(data.message || `${aircraftId} added to landing queue`);
            loadDashboard();
        } else {
            showError(data.error || 'Failed to add to landing queue');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to add aircraft to landing queue');
    }
}

function formatRequestedTime(value) {
    if (!value) return '';

    const normalized = String(value).replace(' ', 'T');
    const dt = new Date(normalized);

    if (isNaN(dt.getTime())) {
        return value;
    }

    return dt.toLocaleTimeString([], {
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Keep old function name too, in case anything else still calls it
async function addToLandingQueue(aircraftId) {
    openLandingModal(aircraftId);
}

function formatScheduledTime(value) {
    if (!value) return '';

    const normalized = String(value).replace(' ', 'T');
    const dt = new Date(normalized);

    if (isNaN(dt.getTime())) {
        return value;
    }

    return dt.toLocaleString([], {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
    });
}

// Render landing queue
function renderLandingQueue(queue) {
    const container = document.getElementById('landingQueueList');
    container.innerHTML = '';

    if (!queue || queue.length === 0) {
        container.innerHTML = '<p style="color: #64748b;">No aircraft in landing queue.</p>';
        return;
    }

    queue.forEach((item, index) => {
        const scheduledHtml = item.scheduled_landing_time
            ? `<br><small>🕐 Scheduled: ${formatScheduledTime(item.scheduled_landing_time)}</small>`
            : '<br><small style="color: #64748b;">No scheduled time</small>';

        const assignedHtml = item.assigned_runway_id
            ? `<br><small style="color: #10b981;">✓ Assigned to Runway ${item.assigned_runway_id}</small>`
            : '';

        const queueItem = document.createElement('div');
        queueItem.className = 'queue-item';

        queueItem.innerHTML = `
            <div class="queue-item-priority">${item.priority ?? index + 1}</div>
            <div class="queue-item-details">
                <strong>Aircraft ${item.aircraft_id}</strong><br>
                <small>Requested: ${formatRequestedTime(item.requested_at)}</small>
                ${scheduledHtml}
                ${assignedHtml}
            </div>
            <button class="btn btn-danger btn-small" onclick="removeFromLandingQueue('${item.aircraft_id}')">Remove</button>
        `;

        container.appendChild(queueItem);
    });
}

// Backward compatibility with your old function name
function updateLandingQueue(queue) {
    renderLandingQueue(queue);
}

// Remove from landing queue
async function removeFromLandingQueue(aircraftId) {
    try {
        const response = await fetch(`${API_BASE_URL}/landing-queue/${aircraftId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess(data.message);
            loadDashboard();
        } else {
            showError(data.error || 'Failed to remove from landing queue');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to remove from landing queue');
    }
}

// Backward compatibility with your old function name
async function removeFromQueue(aircraftId) {
    await removeFromLandingQueue(aircraftId);
}

// Process next landing queue item
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
            let message = data.error || 'Failed to process queue';

            if (data.details && Array.isArray(data.details) && data.details.length > 0) {
                message += '\n\n' + data.details.join('\n');
            }

            showError(message);
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to process landing queue');
    }
}

async function completeLanding(aircraftId) {
    try {
        const response = await fetch(`${API_BASE_URL}/aircraft/${aircraftId}/complete-landing`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess(data.message || `Aircraft ${aircraftId} completed landing`);
            loadDashboard();
        } else {
            showError(data.error || 'Failed to complete landing');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to complete landing');
    }
}

// Request takeoff
function requestTakeoff(aircraftId) {
    pendingTakeoffAircraftId = aircraftId;

    const now = new Date();
    now.setSeconds(0, 0);

    const localISO = new Date(now - now.getTimezoneOffset() * 60000)
        .toISOString()
        .slice(0, 16);

    const timeInput = document.getElementById('takeoffTimeInput');
    const label = document.getElementById('takeoffModalAircraftLabel');
    const modal = document.getElementById('takeoffTimeModal');

    if (!timeInput || !label || !modal) {
        showError('Takeoff modal HTML is missing from index.html');
        return;
    }

    timeInput.value = localISO;
    label.textContent = `Aircraft: ${aircraftId}`;
    modal.style.display = 'flex';
}

function closeTakeoffModal() {
    const modal = document.getElementById('takeoffTimeModal');
    if (modal) {
        modal.style.display = 'none';
    }
    pendingTakeoffAircraftId = null;
}

async function confirmTakeoffRequest() {
    const aircraftId = pendingTakeoffAircraftId;
    if (!aircraftId) {
        showError('No aircraft selected for takeoff request');
        return;
    }

    const rawTime = document.getElementById('takeoffTimeInput')?.value;

    try {
        const response = await fetch(`${API_BASE_URL}/takeoff-queue`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                aircraft_id: aircraftId
            })
        });

        const data = await response.json();

        if (response.ok) {
            closeTakeoffModal();
            showSuccess(data.message || `${aircraftId} added to takeoff queue`);
            loadDashboard();
        } else {
            showError(data.error || 'Failed to add to takeoff queue');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to add aircraft to takeoff queue');
    }
}

// Process next takeoff queue item
async function processNextTakeoff() {
    try {
        const response = await fetch(`${API_BASE_URL}/takeoff-queue/process-next`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess(data.message || 'Processed next takeoff request');
            loadDashboard();
        } else {
            let message = data.error || 'Failed to process takeoff queue';

            if (data.details && Array.isArray(data.details) && data.details.length > 0) {
                message += '\n\n' + data.details.join('\n');
            }

            showError(message);
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to process takeoff queue');
    }
}

// Remove from takeoff queue
async function removeFromTakeoffQueue(aircraftId) {
    try {
        const response = await fetch(`${API_BASE_URL}/takeoff-queue/${aircraftId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess(data.message || `${aircraftId} removed from takeoff queue`);
            loadDashboard();
        } else {
            showError(data.error || 'Failed to remove from takeoff queue');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to remove from takeoff queue');
    }
}

// Render takeoff queue
function renderTakeoffQueue(queue) {
    const container = document.getElementById('takeoffQueueList');

    if (!container) {
        return;
    }

    container.innerHTML = '';

    if (!queue || queue.length === 0) {
        container.innerHTML = '<p style="color: #64748b;">No aircraft in takeoff queue.</p>';
        return;
    }

    queue.forEach((item, index) => {
        const queueItem = document.createElement('div');
        queueItem.className = 'queue-item';

        queueItem.innerHTML = `
            <div class="queue-item-priority">${index + 1}</div>
            <div class="queue-item-details">
                <strong>Aircraft ${item.aircraft_id}</strong><br>
                <small>Requested: ${formatRequestedTime(item.requested_at)}</small>
                ${item.assigned_runway_id ? `<br><small style="color: #10b981;">✓ Assigned to Runway ${item.assigned_runway_id}</small>` : ''}
            </div>
            <button class="btn btn-danger btn-small" onclick="removeFromTakeoffQueue('${item.aircraft_id}')">Remove</button>
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
            headers: { 'Content-Type': 'application/json' },
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
        length: parseInt(document.getElementById('runwayLength').value, 10)
    };

    try {
        const response = await fetch(`${API_BASE_URL}/runways`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
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
window.onclick = function (event) {
    if (event.target.id === 'landingTimeModal') {
        closeLandingModal();
        return;
    }

    if (event.target.id === 'takeoffTimeModal') {
        closeTakeoffModal();
        return;
    }

    if (event.target.className === 'modal') {
        event.target.style.display = 'none';
    }
};

// Notification functions
function showSuccess(message) {
    alert('✓ ' + message);
}

function showError(message) {
    alert('✗ ' + message);
}