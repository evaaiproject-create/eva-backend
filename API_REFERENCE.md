# API Reference

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## Endpoints

### Authentication Endpoints

#### POST /auth/register
Register a new user with Google OAuth.

**Request Body:**
```json
{
  "id_token": "string",     // Google ID token from OAuth flow
  "device_id": "string"     // Optional: Device identifier
}
```

**Response (201 Created):**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "user": {
    "uid": "string",
    "email": "string",
    "display_name": "string",
    "role": "user",
    "created_at": "2024-01-01T00:00:00",
    "last_login": "2024-01-01T00:00:00",
    "devices": ["string"],
    "preferences": {}
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid token
- `403 Forbidden` - User limit reached
- `409 Conflict` - User already exists

---

#### POST /auth/login
Login an existing user.

**Request Body:**
```json
{
  "id_token": "string",
  "device_id": "string"     // Optional
}
```

**Response (200 OK):** Same as register

**Error Responses:**
- `400 Bad Request` - Invalid token
- `404 Not Found` - User not found

---

#### GET /auth/verify
Verify if a JWT token is valid.

**Query Parameters:**
- `token` (string, required) - JWT token to verify

**Response (200 OK):**
```json
{
  "valid": true
}
```

---

### User Endpoints

#### GET /users/me
Get current user profile.

**Authentication:** Required

**Response (200 OK):**
```json
{
  "uid": "string",
  "email": "string",
  "display_name": "string",
  "role": "user",
  "created_at": "2024-01-01T00:00:00",
  "last_login": "2024-01-01T00:00:00",
  "devices": ["string"],
  "preferences": {}
}
```

---

#### GET /users/me/devices
Get list of registered devices for current user.

**Authentication:** Required

**Response (200 OK):**
```json
["device_001", "device_002"]
```

---

#### POST /users/me/devices/{device_id}
Register a new device for the current user.

**Authentication:** Required

**Path Parameters:**
- `device_id` (string, required) - Unique device identifier

**Response (200 OK):**
```json
{
  "message": "Device device_001 added successfully"
}
```

---

#### GET /users/me/preferences
Get user preferences.

**Authentication:** Required

**Response (200 OK):**
```json
{
  "theme": "dark",
  "notifications": true,
  "language": "en"
}
```

---

#### PUT /users/me/preferences
Update user preferences.

**Authentication:** Required

**Request Body:**
```json
{
  "theme": "dark",
  "notifications": true,
  "custom_setting": "value"
}
```

**Response (200 OK):**
```json
{
  "message": "Preferences updated successfully"
}
```

---

### Session Endpoints (Cross-Device Sync)

#### POST /sessions
Create a new session for cross-device synchronization.

**Authentication:** Required

**Request Body:**
```json
{
  "device_id": "string",
  "initial_data": {
    "key": "value"
  }
}
```

**Response (201 Created):**
```json
{
  "session_id": "string",
  "user_id": "string",
  "device_id": "string",
  "data": {},
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "expires_at": null
}
```

---

#### GET /sessions
Get all sessions for current user.

**Authentication:** Required

**Response (200 OK):**
```json
[
  {
    "session_id": "string",
    "user_id": "string",
    "device_id": "string",
    "data": {},
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
    "expires_at": null
  }
]
```

---

#### GET /sessions/{session_id}
Get a specific session by ID.

**Authentication:** Required

**Path Parameters:**
- `session_id` (string, required) - Session identifier

**Response (200 OK):** SessionData object

**Error Responses:**
- `403 Forbidden` - Session doesn't belong to user
- `404 Not Found` - Session not found

---

#### PUT /sessions/{session_id}
Update session data.

**Authentication:** Required

**Path Parameters:**
- `session_id` (string, required) - Session identifier

**Request Body:**
```json
{
  "conversation_state": "active",
  "last_action": "user_query",
  "context": {}
}
```

**Response (200 OK):** Updated SessionData object

---

#### DELETE /sessions/{session_id}
Delete a session.

**Authentication:** Required

**Path Parameters:**
- `session_id` (string, required) - Session identifier

**Response (200 OK):**
```json
{
  "message": "Session deleted successfully"
}
```

---

### Function Calling Endpoints

#### GET /functions
List all available functions.

**Authentication:** Required

**Response (200 OK):**
```json
{
  "echo": {
    "description": "Echo back a message",
    "parameters_schema": {
      "type": "object",
      "properties": {
        "message": {"type": "string"}
      },
      "required": ["message"]
    },
    "registered_at": "2024-01-01T00:00:00"
  },
  "calculate": {
    "description": "Perform basic arithmetic",
    "parameters_schema": {...}
  }
}
```

---

#### POST /functions/call
Execute a function by name.

**Authentication:** Required

**Request Body:**
```json
{
  "function_name": "calculate",
  "parameters": {
    "operation": "add",
    "a": 5,
    "b": 3
  },
  "device_id": "device_001"  // Optional
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "result": {
    "result": 8
  },
  "error": null,
  "execution_time": 0.001
}
```

**Error Response (function error):**
```json
{
  "success": false,
  "result": null,
  "error": "Error message",
  "execution_time": 0.001
}
```

---

#### GET /functions/history
Get function call history for current user.

**Authentication:** Required

**Query Parameters:**
- `limit` (integer, optional, default=50, max=100) - Number of records

**Response (200 OK):**
```json
[
  {
    "function_name": "calculate",
    "parameters": {"operation": "add", "a": 5, "b": 3},
    "user_id": "string",
    "result": {"success": true, "result": {"result": 8}},
    "timestamp": "2024-01-01T00:00:00"
  }
]
```

---

### System Endpoints

#### GET /
Get API information.

**Response (200 OK):**
```json
{
  "name": "Eva Backend API",
  "version": "0.1.0",
  "status": "operational",
  "description": "Personal assistant backend inspired by JARVIS and Baymax",
  "documentation": "/docs"
}
```

---

#### GET /health
Health check endpoint.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "environment": "development",
  "max_users": 5
}
```

---

## Rate Limits

Currently no rate limits are enforced. For production deployment, consider implementing:
- Per-user rate limits
- Per-endpoint rate limits
- Token bucket or sliding window algorithms

## Error Responses

All error responses follow this format:
```json
{
  "detail": "Error message"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (resource already exists)
- `500` - Internal Server Error
