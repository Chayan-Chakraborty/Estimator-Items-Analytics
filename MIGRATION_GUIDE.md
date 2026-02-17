# Migration Guide - API v1.0.0

## Overview

This guide outlines the changes made to refactor the API structure and add versioning with the `/v1/api/analytics` prefix.

## Breaking Changes

### API Endpoint URLs

All API endpoints now require the `/v1/api/analytics` prefix.

#### Before (Old URLs)
```
http://localhost:8090/search-items
http://localhost:8090/fetch-items
http://localhost:8090/ingest
http://localhost:8090/config
```

#### After (New URLs)
```
http://localhost:8090/v1/api/analytics/search-items
http://localhost:8090/v1/api/analytics/fetch-items
http://localhost:8090/v1/api/analytics/ingest
http://localhost:8090/v1/api/analytics/config
```

## Code Structure Changes

### Route Organization

Routes have been reorganized from a single monolithic `controller.py` file into modular route files:

#### New Structure
```
backend/routes/
├── __init__.py              # Package initializer
├── controller.py            # Main FastAPI app with router configuration
├── items_routes.py          # Item-related endpoints (10 routes)
├── search_routes.py         # Search endpoints (3 routes)
├── ingest_routes.py         # Data ingestion endpoint (1 route)
├── config_routes.py         # Configuration endpoint (1 route)
└── auth_routes.py           # Authentication endpoint (1 route)
```

### Route Categories

#### 1. Items Routes (`items_routes.py`)
- `/fetch-items` - Fetch from external API
- `/vishanti-items` - Fetch from Qdrant
- `/vishanti-items-view` - Aggregated pricing view
- `/add-items-to-qdrant` - Direct item insertion
- `/extract-item` - Single item extraction
- `/extract-items-with-identifiers` - Multiple items extraction
- `/extract-items-with-identifiers-fuzzy` - Fuzzy extraction
- `/items-by-identifiers` - Fetch by IDs
- `/items-with-identifiers` - Update resources file

#### 2. Search Routes (`search_routes.py`)
- `/search-fuzz` - Fuzzy text search
- `/search` - Legacy search (deprecated)
- `/search-items` - Main search endpoint

#### 3. Ingest Routes (`ingest_routes.py`)
- `/ingest` - Data ingestion

#### 4. Config Routes (`config_routes.py`)
- `/config` - App configuration

#### 5. Auth Routes (`auth_routes.py`)
- `/get-auth-token` - Authentication token

## Configuration Changes

### Docker Compose

**File:** `docker-compose.yml`

**What Changed:** Updated volume mount path to reflect the new folder name

```yaml
# Before
volumes:
  - /Users/chayanchakraborty/Documents/python_new_dir/voice-text-search-platform/backend/resources:/app/resources

# After
volumes:
  - /Users/chayanchakraborty/Documents/python_new_dir/Estimator-Items-Analytics/backend/resources:/app/resources
```

### Entrypoint Script

**File:** `backend/entrypoint.sh`

**What Changed:** Updated uvicorn command to reference the new route structure

```bash
# Before
uvicorn controller:app --host 0.0.0.0 --port 8090

# After
uvicorn routes.controller:app --host 0.0.0.0 --port 8090
```

### Frontend Configuration

**File:** `frontend/index.html`

**What Changed:** Updated API base URL to include the new prefix

```javascript
// Before
const API_BASE = "http://localhost:8090";

// After
const API_BASE = "http://localhost:8090/v1/api/analytics";
```

## Migration Checklist

If you have custom integrations or scripts, update them as follows:

- [ ] Update all API endpoint URLs to include `/v1/api/analytics` prefix
- [ ] Rebuild Docker containers: `docker-compose up --build`
- [ ] Test all endpoints using the new URLs
- [ ] Update any external API consumers (mobile apps, scripts, etc.)
- [ ] Update API documentation or postman collections

## Testing the Migration

### 1. Health Check
```bash
curl http://localhost:8090/health
curl http://localhost:8090/
```

### 2. Config Endpoint
```bash
curl http://localhost:8090/v1/api/analytics/config
```

### 3. Search Endpoint
```bash
curl "http://localhost:8090/v1/api/analytics/search-items?query=bed"
```

### 4. Interactive API Docs
Visit: http://localhost:8090/docs

All endpoints are now organized by tags (Items, Search, Ingest, Config, Auth) for better navigation.

## Benefits of These Changes

1. **Better Organization**: Routes are logically grouped by functionality
2. **API Versioning**: `/v1` prefix allows for future API versions without breaking changes
3. **Maintainability**: Smaller, focused route files are easier to maintain
4. **Scalability**: Easy to add new route categories as the project grows
5. **Clear Namespace**: `/api/analytics` prefix clearly identifies the API purpose
6. **Better Documentation**: Organized routes with tags in OpenAPI docs

## Rollback Instructions

If you need to rollback:

1. Restore the original `controller.py` from git history
2. Delete the new route files (`items_routes.py`, etc.)
3. Update `entrypoint.sh` to use `controller:app`
4. Update `frontend/index.html` to remove the prefix
5. Rebuild containers: `docker-compose down && docker-compose up --build`

## Support

If you encounter any issues during migration, check:

1. Docker containers are rebuilt: `docker-compose up --build`
2. All environment variables are set correctly
3. Volume mounts in `docker-compose.yml` point to correct paths
4. No cached API responses in your client application

For additional help, review the logs:
```bash
docker-compose logs backend
docker-compose logs frontend
```
