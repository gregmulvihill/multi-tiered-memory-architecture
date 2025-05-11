# Multi-Tiered Memory Architecture API Reference

## 1. Overview

The Multi-Tiered Memory Architecture (MTMA) exposes a RESTful API for LLM contexts to interact with the memory system. This document provides a detailed reference for all available endpoints, request/response formats, and usage examples.

## 2. API Conventions

### 2.1 Base URL

All API endpoints are accessible under the base URL: `http://[host]:[port]/`

### 2.2 Content Types

- Request bodies should be formatted as JSON (`application/json`)
- Response bodies are formatted as JSON (`application/json`)

### 2.3 Authentication

The API uses OAuth 2.0 Bearer tokens for authentication:

```
Authorization: Bearer <token>
```

### 2.4 Error Handling

Errors are returned with appropriate HTTP status codes and a JSON body containing details:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

## 3. API Endpoints

### 3.1 Health Check

#### GET /health

Checks the health of the API and its connected services.

**Response (200 OK)**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### 3.2 Short-Term Memory Endpoints

#### POST /memory/short-term

Creates a new short-term memory.

**Request Body**
```json
{
  "content": "string",
  "metadata": {
    "category": "string",
    "tags": ["string"],
    "importance": "number"
  },
  "ttl": "number" // Optional, in seconds
}
```

**Response (201 Created)**
```json
{
  "id": "string",
  "created_at": "timestamp"
}
```

#### GET /memory/short-term/{memory_id}

Retrieves a short-term memory by ID.

**Path Parameters**
- `memory_id`: The ID of the memory to retrieve

**Response (200 OK)**
```json
{
  "_id": "string",
  "content": "string",
  "metadata": {
    "category": "string",
    "tags": ["string"],
    "importance": "number"
  },
  "_created_at": "timestamp",
  "_access_count": "number",
  "_last_accessed_at": "timestamp"
}
```

**Response (404 Not Found)**
```json
{
  "error": {
    "code": "memory_not_found",
    "message": "Memory not found"
  }
}
```

#### PUT /memory/short-term/{memory_id}

Updates an existing short-term memory.

**Path Parameters**
- `memory_id`: The ID of the memory to update

**Request Body**
```json
{
  "content": "string",
  "metadata": {
    "category": "string",
    "tags": ["string"],
    "importance": "number"
  }
}
```

**Response (200 OK)**
```json
{
  "id": "string",
  "updated_at": "timestamp"
}
```

#### DELETE /memory/short-term/{memory_id}

Deletes a short-term memory.

**Path Parameters**
- `memory_id`: The ID of the memory to delete

**Response (204 No Content)**

#### POST /memory/short-term/{memory_id}/extend

Extends the TTL of a short-term memory.

**Path Parameters**
- `memory_id`: The ID of the memory to extend

**Request Body**
```json
{
  "ttl": "number" // In seconds
}
```

**Response (200 OK)**
```json
{
  "id": "string",
  "expires_at": "timestamp"
}
```

#### POST /memory/short-term/{memory_id}/lock

Locks a memory to prevent automatic decay.

**Path Parameters**
- `memory_id`: The ID of the memory to lock

**Response (200 OK)**
```json
{
  "id": "string",
  "locked": true,
  "locked_at": "timestamp"
}
```

#### POST /memory/short-term/{memory_id}/unlock

Unlocks a memory, restoring its TTL.

**Path Parameters**
- `memory_id`: The ID of the memory to unlock

**Request Body**
```json
{
  "ttl": "number" // Optional, in seconds
}
```

**Response (200 OK)**
```json
{
  "id": "string",
  "locked": false,
  "expires_at": "timestamp"
}
```

#### GET /memory/short-term/search

Searches for short-term memories matching a query.

**Query Parameters**
- `query`: JSON-encoded search query
- `limit`: Maximum number of results (default: 100)

**Response (200 OK)**
```json
{
  "results": [
    {
      "_id": "string",
      "content": "string",
      "metadata": {
        "category": "string",
        "tags": ["string"],
        "importance": "number"
      },
      "_created_at": "timestamp"
    }
  ],
  "count": "number"
}
```

### 3.3 Long-Term Memory Endpoints

#### POST /memory/long-term

Creates a new long-term memory.

**Request Body**
```json
{
  "content": "string",
  "metadata": {
    "category": "string",
    "tags": ["string"],
    "confidence": "number"
  },
  "relationships": [
    {
      "type": "string",
      "target_id": "string",
      "properties": {}
    }
  ]
}
```

**Response (201 Created)**
```json
{
  "id": "string",
  "created_at": "timestamp"
}
```

#### GET /memory/long-term/{memory_id}

Retrieves a long-term memory by ID.

**Path Parameters**
- `memory_id`: The ID of the memory to retrieve

**Response (200 OK)**
```json
{
  "_id": "string",
  "content": "string",
  "metadata": {
    "category": "string",
    "tags": ["string"],
    "confidence": "number"
  },
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "version": "number",
  "relationships": [
    {
      "type": "string",
      "target_id": "string",
      "properties": {}
    }
  ]
}
```

#### PUT /memory/long-term/{memory_id}

Updates an existing long-term memory.

**Path Parameters**
- `memory_id`: The ID of the memory to update

**Request Body**
```json
{
  "content": "string",
  "metadata": {
    "category": "string",
    "tags": ["string"],
    "confidence": "number"
  }
}
```

**Response (200 OK)**
```json
{
  "id": "string",
  "updated_at": "timestamp",
  "version": "number"
}
```

#### DELETE /memory/long-term/{memory_id}

Deletes a long-term memory.

**Path Parameters**
- `memory_id`: The ID of the memory to delete

**Response (204 No Content)**

#### GET /memory/long-term/search

Searches for long-term memories matching a query.

**Query Parameters**
- `query`: JSON-encoded search query
- `limit`: Maximum number of results (default: 100)

**Response (200 OK)**
```json
{
  "results": [
    {
      "_id": "string",
      "content": "string",
      "metadata": {
        "category": "string",
        "tags": ["string"],
        "confidence": "number"
      },
      "created_at": "timestamp",
      "updated_at": "timestamp",
      "version": "number"
    }
  ],
  "count": "number"
}
```

#### POST /memory/long-term/similarity

Finds memories similar to a provided text or vector embedding.

**Request Body**
```json
{
  "text": "string", // Optional
  "embedding": [0.1, 0.2, ...], // Optional, float array
  "limit": "number", // Default: 10
  "threshold": "number" // Default: 0.7, minimum similarity score
}
```

**Response (200 OK)**
```json
{
  "results": [
    {
      "_id": "string",
      "content": "string",
      "metadata": {
        "category": "string",
        "tags": ["string"],
        "confidence": "number"
      },
      "similarity": "number"
    }
  ]
}
```

### 3.4 Memory Lifecycle Endpoints

#### POST /memory/consolidate

Manually triggers memory consolidation for eligible memories.

**Request Body**
```json
{
  "threshold": "number", // Optional, minimum access count
  "limit": "number" // Optional, maximum memories to consolidate
}
```

**Response (200 OK)**
```json
{
  "consolidated": "number",
  "elapsed_time": "number"
}
```

#### POST /memory/retrieve/{memory_id}

Retrieves a memory from long-term storage to short-term storage.

**Path Parameters**
- `memory_id`: The ID of the long-term memory to retrieve

**Request Body**
```json
{
  "ttl": "number" // Optional, in seconds
}
```

**Response (200 OK)**
```json
{
  "stm_id": "string",
  "ltm_id": "string",
  "expires_at": "timestamp"
}
```

#### POST /memory/forget/{memory_id}

Permanently forgets a memory from long-term storage.

**Path Parameters**
- `memory_id`: The ID of the long-term memory to forget

**Response (204 No Content)**

### 3.5 World State Endpoints

#### GET /world-state

Get the current world state.

**Response (200 OK)**
```json
{
  "version": "number",
  "state": {},
  "updated_at": "timestamp"
}
```

#### POST /world-state/update

Update the world state.

**Request Body**
```json
{
  "updates": {}
}
```

**Response (200 OK)**
```json
{
  "version": "number",
  "updated_at": "timestamp"
}
```

#### GET /world-state/version/{version}

Get a specific version of the world state.

**Path Parameters**
- `version`: The version number to retrieve

**Response (200 OK)**
```json
{
  "version": "number",
  "state": {},
  "updated_at": "timestamp"
}
```

**Response (404 Not Found)**
```json
{
  "error": {
    "code": "version_not_found",
    "message": "World state version not found"
  }
}
```

#### POST /world-state/rollback/{version}

Rollback the world state to a specific version.

**Path Parameters**
- `version`: The version number to rollback to

**Response (200 OK)**
```json
{
  "version": "number", // New version number
  "rolled_back_from": "number",
  "rolled_back_to": "number",
  "updated_at": "timestamp"
}
```

## 4. Usage Examples

### 4.1 Creating and Retrieving a Short-Term Memory

```python
import requests
import json

# Create a short-term memory
create_memory_url = "http://localhost:8000/memory/short-term"
memory_data = {
    "content": "User asked about project timeline",
    "metadata": {
        "category": "user_interaction",
        "tags": ["timeline", "project"],
        "importance": 3
    },
    "ttl": 3600  # 1 hour
}
response = requests.post(create_memory_url, json=memory_data)
memory_id = response.json()["id"]

# Retrieve the memory
get_memory_url = f"http://localhost:8000/memory/short-term/{memory_id}"
response = requests.get(get_memory_url)
memory = response.json()
print(f"Memory content: {memory['content']}")
print(f"Access count: {memory['_access_count']}")
```

### 4.2 Updating the World State

```python
import requests
import json

# Get current world state
get_state_url = "http://localhost:8000/world-state"
response = requests.get(get_state_url)
current_state = response.json()
print(f"Current state version: {current_state['version']}")

# Update the world state
update_state_url = "http://localhost:8000/world-state/update"
updates = {
    "updates": {
        "user_status": "active",
        "current_task": "project_planning",
        "task_progress": 0.3
    }
}
response = requests.post(update_state_url, json=updates)
updated_state = response.json()
print(f"New state version: {updated_state['version']}")
```

### 4.3 Similarity Search

```python
import requests
import json

# Find memories similar to a text
similarity_url = "http://localhost:8000/memory/long-term/similarity"
search_data = {
    "text": "project timeline for Q3 deliverables",
    "limit": 5,
    "threshold": 0.6
}
response = requests.post(similarity_url, json=search_data)
similar_memories = response.json()["results"]

for memory in similar_memories:
    print(f"Memory: {memory['content']}")
    print(f"Similarity: {memory['similarity']}")
    print("---")
```

## 5. Rate Limits

The API enforces the following rate limits:

- 100 requests per minute per API key
- 5,000 requests per day per API key
- Maximum request body size: 1MB

Exceeding these limits will result in HTTP 429 Too Many Requests responses.

## 6. Versioning

The API is versioned using semantic versioning (MAJOR.MINOR.PATCH). The current version is accessible via the `/health` endpoint.

Future breaking changes will be introduced with a new major version number.