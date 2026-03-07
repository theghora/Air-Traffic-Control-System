# API Documentation - Air Traffic Control System

## Overview

The ATC System API provides RESTful endpoints for managing aircraft, runways, flights, and queue operations. All endpoints return JSON responses.

## Base URL

```
http://localhost:5000/api
```

## Authentication

Currently, the API does not require authentication. For production deployment, implement JWT or OAuth2 authentication.

## Response Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 201  | Created |
| 400  | Bad Request - Validation error or constraint violation |
| 404  | Not Found - Resource doesn't exist |
| 500  | Internal Server Error |

## Endpoints Reference

### System

#### GET /api/health

Check system health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-07T12:00:00.000Z"
}
```

### Aircraft

#### GET /api/aircraft

Get all aircraft.

**Response:**
```json
[
  {
    "id": "AC001",
    "model": "Boeing 737",
    "size": "Medium",
    "status": "In-Air",
    "current_runway_id": null,
    "current_gate_id": null,
    "altitude": 10000,
    "speed": 250,
    "last_updated": "2026-03-07T12:00:00.000Z"
  }
]
```

#### GET /api/aircraft/{aircraft_id}

Get specific aircraft by ID.

**Parameters:**
- `aircraft_id` (path) - Aircraft identifier

**Response:**
```json
{
  "id": "AC001",
  "model": "Boeing 737",
  "size": "Medium",
  "status": "In-Air",
  "altitude": 10000,
  "speed": 250
}
```

#### POST /api/aircraft

Create new aircraft.

**Request Body:**
```json
{
  "id": "AC007",
  "model": "Boeing 747",
  "size": "Heavy",
  "status": "Parked",
  "altitude": 0,
  "speed": 0
}
```

**Constraints:**
- `size`: Must be "Small", "Medium", or "Heavy"
- `status`: Must be "In-Air", "Landing", "Taxiing", "Parked", or "Takeoff"

**Response:** (201 Created)
```json
{
  "id": "AC007",
  "model": "Boeing 747",
  "size": "Heavy",
  "status": "Parked"
}
```

#### PUT /api/aircraft/{aircraft_id}/status

Update aircraft status.

**Parameters:**
- `aircraft_id` (path) - Aircraft identifier

**Request Body:**
```json
{
  "status": "In-Air",
  "altitude": 15000,
  "speed": 300
}
```

**Valid Status Transitions:**
- In-Air → Landing
- Landing → Taxiing, In-Air
- Taxiing → Parked, Takeoff
- Parked → Taxiing
- Takeoff → In-Air

**Error Response:** (400)
```json
{
  "error": "Invalid status transition from Parked to In-Air"
}
```

### Runways

#### GET /api/runways

Get all runways.

**Response:**
```json
[
  {
    "id": 1,
    "name": "RW-09L",
    "length": 3500,
    "status": "Available",
    "occupied_by": null,
    "last_used": null
  },
  {
    "id": 2,
    "name": "RW-09R",
    "length": 3800,
    "status": "Occupied",
    "occupied_by": "AC001",
    "last_used": "2026-03-07T11:55:00.000Z"
  }
]
```

#### GET /api/runways/{runway_id}

Get specific runway by ID.

**Parameters:**
- `runway_id` (path) - Runway identifier

#### POST /api/runways

Create new runway.

**Request Body:**
```json
{
  "name": "RW-18",
  "length": 3200,
  "status": "Available"
}
```

**Constraints:**
- `length`: Minimum 1000, maximum 6000 meters
- `name`: Must be unique

#### POST /api/runways/{runway_id}/assign

Assign runway to aircraft.

**Parameters:**
- `runway_id` (path) - Runway identifier

**Request Body:**
```json
{
  "aircraft_id": "AC001"
}
```

**Constraint Checks Performed:**
1. Runway availability
2. Runway not occupied by another aircraft
3. Runway length suitable for aircraft size
4. Cooldown period elapsed (60 seconds)

**Success Response:**
```json
{
  "message": "Runway RW-09L assigned to aircraft AC001",
  "runway": {
    "id": 1,
    "name": "RW-09L",
    "status": "Occupied",
    "occupied_by": "AC001"
  },
  "aircraft": {
    "id": "AC001",
    "current_runway_id": 1
  }
}
```

**Error Response:** (400)
```json
{
  "error": "Runway RW-09L (length: 2000m) is too short for Heavy aircraft (requires: 3500m)"
}
```

#### POST /api/runways/{runway_id}/release

Release runway after use.

**Parameters:**
- `runway_id` (path) - Runway identifier

**Response:**
```json
{
  "message": "Runway RW-09L released",
  "runway": {
    "id": 1,
    "name": "RW-09L",
    "status": "Available",
    "occupied_by": null
  }
}
```

### Landing Queue

#### GET /api/landing-queue

Get current landing queue (FIFO order).

**Response:**
```json
[
  {
    "id": 1,
    "aircraft_id": "AC004",
    "priority": 1,
    "requested_at": "2026-03-07T11:45:00.000Z",
    "assigned_runway_id": null
  },
  {
    "id": 2,
    "aircraft_id": "AC005",
    "priority": 2,
    "requested_at": "2026-03-07T11:46:00.000Z",
    "assigned_runway_id": 1
  }
]
```

#### POST /api/landing-queue

Add aircraft to landing queue.

**Request Body:**
```json
{
  "aircraft_id": "AC004"
}
```

**Constraints:**
- Aircraft must exist
- Aircraft must be in "In-Air" or "Landing" status

**Response:** (201 Created)
```json
{
  "message": "Aircraft AC004 added to landing queue",
  "queue_item": {
    "id": 1,
    "aircraft_id": "AC004",
    "priority": 1
  }
}
```

#### POST /api/landing-queue/process-next

Process next aircraft in queue and assign runway.

**Algorithm:**
1. Get aircraft with lowest priority number (first in queue)
2. Find suitable available runway
3. Assign runway to aircraft
4. Update statuses

**Success Response:**
```json
{
  "message": "Runway assigned to next aircraft in queue",
  "queue_item": {
    "id": 1,
    "aircraft_id": "AC004",
    "assigned_runway_id": 1
  }
}
```

**Error Response:** (400)
```json
{
  "error": "No suitable runway available"
}
```

#### DELETE /api/landing-queue/{aircraft_id}

Remove aircraft from landing queue.

**Parameters:**
- `aircraft_id` (path) - Aircraft identifier

**Response:**
```json
{
  "message": "Aircraft AC004 removed from landing queue"
}
```

### Conflicts

#### GET /api/conflicts

Detect all current conflicts.

**Response:**
```json
{
  "conflicts": [
    {
      "type": "runway_multi_assign",
      "runway": "RW-09L",
      "aircraft": ["AC001", "AC002"],
      "severity": "CRITICAL"
    },
    {
      "type": "invalid_queue_status",
      "aircraft_id": "AC003",
      "status": "Parked",
      "message": "Aircraft AC003 in landing queue but status is Parked",
      "severity": "MEDIUM"
    }
  ],
  "count": 2,
  "has_critical": true
}
```

**Conflict Types:**
- `runway_multi_assign`: Multiple aircraft on same runway (CRITICAL)
- `duplicate_priority`: Multiple aircraft with same queue priority (HIGH)
- `invalid_queue_status`: Aircraft in queue with wrong status (MEDIUM)

### Dashboard

#### GET /api/dashboard

Get aggregated dashboard data.

**Response:**
```json
{
  "aircraft": {
    "total": 6,
    "in_air": 2,
    "landing": 1,
    "taxiing": 1,
    "parked": 2,
    "list": [...]
  },
  "runways": {
    "total": 4,
    "available": 2,
    "occupied": 2,
    "list": [...]
  },
  "gates": {
    "total": 10,
    "available": 8,
    "occupied": 2
  },
  "landing_queue": {
    "count": 2,
    "queue": [...]
  },
  "conflicts": {
    "count": 0,
    "has_critical": false,
    "list": []
  }
}
```

## Runway Length Requirements

| Aircraft Size | Minimum Runway Length |
|--------------|----------------------|
| Small        | 1,500m              |
| Medium       | 2,500m              |
| Heavy        | 3,500m              |

## Status Transition Diagram

```
┌─────────┐
│ Parked  │───────────┐
└─────────┘           │
                      ▼
                 ┌─────────┐      ┌─────────┐
                 │ Taxiing │◄─────┤ Landing │
                 └─────────┘      └─────────┘
                      │                │
                      │                │
                      ▼                ▼
                 ┌─────────┐      ┌─────────┐
                 │ Takeoff │─────►│ In-Air  │
                 └─────────┘      └─────────┘
```

## Error Handling

All error responses follow this format:

```json
{
  "error": "Detailed error message"
}
```

Common errors:
- **Constraint Violation**: Runway too short, already occupied, etc.
- **Invalid Transition**: Status change not allowed
- **Not Found**: Resource doesn't exist
- **Validation Error**: Missing or invalid fields

## Rate Limiting

Currently no rate limiting is implemented. For production:
- Implement rate limiting per IP/API key
- Recommended: 100 requests per minute per client

## WebSocket Support (Future)

For real-time updates without polling:
- Connect to `ws://localhost:5000/ws`
- Receive push notifications for status changes
- Subscribe to specific aircraft or runways

## Versioning

Current version: v1 (implicit in `/api` prefix)

Future versions will be accessible via:
- `/api/v2/...`
- Header: `Accept: application/vnd.atc.v2+json`
