# Veritas Backend API Documentation

**File:** `docs/API.md`  
**Version:** 1.0.0  
**Base URL:** `https://veritas-api-{username}.repl.co`  
**Team:** Console.log(Win)

---

## Overview

Veritas Backend API provides secure, AI-powered communication endpoints for UKNF financial supervision. Built with FastAPI, featuring OpenID Connect authentication and real-time WebSocket notifications.

## Authentication

### OIDC Flow
```http
GET /api/auth/login
# Returns authorization URL for OIDC provider

POST /api/auth/callback  
# Handles OIDC callback with authorization code
```

### Session Management
```http
GET /api/auth/me
# Get current user profile

POST /api/auth/logout
# Clear user session
```

## Core Endpoints

### Report Management

#### Submit Report
```http
POST /api/reports
Content-Type: multipart/form-data

Fields:
- entity_code: string (required) - Entity identifier (e.g., "MBANK001")
- report_type: string (required) - "liquidity" | "aml" | "capital" | "governance" 
- file: file (required) - XLSX report file (max 50MB)

Response:
{
    "id": "report-uuid",
    "entity_code": "MBANK001", 
    "entity_name": "mBank S.A.",
    "report_type": "liquidity",
    "status": "submitted",
    "validation_confidence": 0.94,
    "risk_score": 3.2,
    "risk_level": "low"
}
```

#### Get Reports
```http
GET /api/reports?status=submitted&limit=50

Query Parameters:
- status: "draft" | "submitted" | "approved" | "rejected" (optional)
- entity_code: string (optional) - Filter by entity  
- limit: integer (optional, default: 50, max: 1000)

Response:
[
    {
        "id": "report-uuid",
        "entity_code": "MBANK001",
        "status": "submitted",
        "submitted_at": "2025-10-04T14:30:00Z",
        "risk_score": 3.2,
        "validation_errors": []
    }
]
```

#### Get Report Details
```http
GET /api/reports/{report_id}

Response:
{
    "id": "report-uuid",
    "entity_code": "MBANK001",
    "entity_name": "mBank S.A.", 
    "report_type": "liquidity",
    "status": "submitted",
    "file_name": "liquidity_report_Q3_2025.xlsx",
    "file_size": 2048576,
    "submitted_by": "user-uuid",
    "submitted_at": "2025-10-04T14:30:00Z",

    "validation_confidence": 0.94,
    "validation_errors": [],
    "validation_warnings": ["Kolumna 'Uwagi' jest pusta w 3 wierszach"],

    "ai_category": "liquidity",
    "risk_score": 3.2,
    "risk_level": "low", 
    "anomalies": [],
    "reasoning_chain": "Analiza wskaźników płynności...",

    "reviewed_at": null,
    "reviewed_by": null,
    "decision_comment": null
}
```

#### Approve Report (UKNF Only)
```http
POST /api/reports/{report_id}/approve
Content-Type: application/x-www-form-urlencoded

Fields:
- comment: string (optional) - Approval comment

Response:
{
    "id": "report-uuid", 
    "status": "approved",
    "reviewed_at": "2025-10-04T15:45:00Z",
    "reviewed_by": "uknf-supervisor-uuid",
    "decision_comment": "Raport zgodny z wymogami"
}
```

#### Reject Report (UKNF Only)  
```http
POST /api/reports/{report_id}/reject
Content-Type: application/x-www-form-urlencoded

Fields:
- comment: string (required) - Rejection reason (min 10 chars)

Response:
{
    "id": "report-uuid",
    "status": "rejected", 
    "reviewed_at": "2025-10-04T15:45:00Z",
    "reviewed_by": "uknf-supervisor-uuid",
    "decision_comment": "Brakujące dane w kolumnie 'Wskaźnik_LCR'"
}
```

### Entity Management

#### Get Entity Directory
```http
GET /api/entities?entity_type=bank&search=mbank

Query Parameters:
- entity_type: "bank" | "insurance" | "investment" | "other" (optional)
- search: string (optional) - Search by name

Response:
[
    {
        "code": "MBANK001", 
        "name": "mBank S.A.",
        "short_name": "mBank",
        "entity_type": "bank",
        "total_reports": 45,
        "approved_reports": 42, 
        "average_risk_score": 3.2
    }
]
```

#### Get Entity Details
```http  
GET /api/entities/{entity_code}

Response:
{
    "code": "MBANK001",
    "name": "mBank S.A.",
    "short_name": "mBank", 
    "nip": "5260250995",
    "krs": "0000025237",
    "lei": "254900GDZFHF2T298714",
    "entity_type": "bank",
    "total_reports": 45,
    "approved_reports": 42,
    "average_risk_score": 3.2
}
```

#### Get Entity Statistics
```http
GET /api/entities/{entity_code}/statistics

Response:
{
    "entity_code": "MBANK001",
    "entity_name": "mBank S.A.",
    "total_reports": 45,
    "approved_reports": 42, 
    "approval_rate": 93.3,
    "average_risk_score": 3.2,
    "is_high_volume": false
}
```

### User Management

#### Get User Profile
```http
GET /api/users/me

Response:
{
    "id": "user-uuid",
    "email": "marta.kowalska@mbank.pl", 
    "name": "Marta Kowalska",
    "roles": ["entity_officer"],
    "entity_access": ["MBANK001"],
    "entity_names": ["mBank S.A."],
    "is_active": true,
    "last_login": "2025-10-04T14:00:00Z"
}
```

#### List Users (Admin Only)
```http
GET /api/users?role=entity_officer&active_only=true

Response:
[
    {
        "id": "user-uuid",
        "email": "marta.kowalska@mbank.pl",
        "name": "Marta Kowalska", 
        "roles": ["entity_officer"],
        "entity_access": ["MBANK001"],
        "is_active": true
    }
]
```

#### Assign Role (Admin Only)
```http
POST /api/users/{user_id}/assign-role?role=uknf_supervisor

Response:
{
    "success": true,
    "message": "Rola uknf_supervisor została przypisana użytkownikowi user@example.com"
}
```

### Health Monitoring

#### Basic Health Check
```http
GET /api/health

Response:
{
    "status": "healthy",
    "service": "Veritas Backend API",
    "version": "1.0.0", 
    "timestamp": "2025-10-04T16:00:00Z"
}
```

#### AI Agents Health
```http
GET /api/health/agents

Response:
{
    "status": "healthy",
    "agents": {
        "validator": {
            "status": "healthy",
            "model": "deepseek-chat"
        },
        "categorizer": {
            "status": "healthy", 
            "model": "deepseek-reasoner"
        },
        "notifier": {
            "status": "healthy",
            "model": "deepseek-chat" 
        }
    },
    "prompt_logging": {
        "enabled": true,
        "log_file": "/app/prompts.md",
        "sessions_logged": 127
    }
}
```

## WebSocket Real-Time Notifications

### Connection
```javascript
const ws = new WebSocket('wss://veritas-api-{username}.repl.co/ws?user_id={user_id}');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Notification:', data);
};
```

### Message Types
```javascript
// Connection Established
{
    "type": "connected",
    "message": "WebSocket connected successfully",
    "user_id": "user-uuid"
}

// Report Approved 
{
    "type": "notification",
    "data": {
        "id": "notification-uuid",
        "title": "Raport zatwierdzony",
        "message": "Twój raport liquidity_report_Q3_2025.xlsx został zatwierdzony przez UKNF",
        "notification_type": "report_approved",
        "created_at": "2025-10-04T15:45:00Z",
        "context": {
            "entity_name": "mBank S.A.",
            "report_type": "liquidity"
        }
    }
}

// Report Rejected
{
    "type": "notification", 
    "data": {
        "id": "notification-uuid",
        "title": "Raport odrzucony",
        "message": "Twój raport wymaga poprawy. Sprawdź uwagi i prześlij ponownie.",
        "notification_type": "report_rejected",
        "context": {
            "reason": "Brakujące dane w kolumnie 'Wskaźnik_LCR'"
        }
    }
}
```

## Error Responses

### Standard Error Format
```json
{
    "error": true,
    "message": "Szczegółowy opis błędu",
    "status_code": 400,
    "path": "/api/reports"
}
```

### Common HTTP Status Codes
```
200 OK - Successful request
201 Created - Resource created successfully  
400 Bad Request - Invalid request data
401 Unauthorized - Authentication required
403 Forbidden - Insufficient permissions
404 Not Found - Resource not found
413 Payload Too Large - File too large (>50MB)
422 Unprocessable Entity - Validation errors
500 Internal Server Error - Server error
```

## Rate Limits

```
General API: 100 requests/minute per user
File Upload: 10 requests/minute per user  
WebSocket: 5 connections per user
```

## Security

### CORS Policy
```
Allowed Origins: 
- https://veritas-uknf.lovable.app
- http://localhost:3000 (development)

Allowed Methods: GET, POST, PUT, DELETE, OPTIONS
Allowed Headers: Authorization, Content-Type
Credentials: Included
```

### Authentication
```
Type: OpenID Connect (OIDC)
Flow: Authorization Code + PKCE
Session: HTTP-Only cookies
Token Expiry: 24 hours
```

## Environment Variables

```bash
# Required for API functionality
DEEPSEEK_API_KEY=sk-your-deepseek-key
OIDC_ISSUER=https://auth.veritas-demo.eu/realms/uknf
OIDC_CLIENT_ID=veritas-webapp
OIDC_CLIENT_SECRET=your-secret
FRONTEND_URL=https://veritas-uknf.lovable.app
SECRET_KEY=your-super-secret-key
```

---

**Console.log("Complete API documentation готов! Ready for frontend integration with Lovable. 📡"); ✅**