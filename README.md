# Estimator-Items-Analytics

A FastAPI-based analytics platform for searching and managing estimator items with multilingual support.

## API Structure

The API follows a modular architecture with routes organized by functionality. All endpoints are prefixed with `/v1/api/analytics`.

### API Endpoints

#### Base URL
- Local: `http://localhost:8090/v1/api/analytics`

#### Search Routes (`/v1/api/analytics`)
- `GET /search-fuzz` - Fuzzy search for quick text matching
- `POST /search` - Legacy search endpoint (deprecated)
- `GET /search-items` - Main search endpoint with multilingual support

#### Items Routes (`/v1/api/analytics`)
- `GET /fetch-items` - Fetch estimator items from external API
- `GET /vishanti-items` - Fetch all items from Vishanti Qdrant collection
- `GET /vishanti-items-view` - Aggregated view with pricing statistics
- `POST /add-items-to-qdrant` - Add items directly to Qdrant
- `GET /extract-item` - Extract single canonical item name from query
- `GET /extract-items-with-identifiers` - Extract all matching items with identifiers
- `GET /extract-items-with-identifiers-fuzzy` - Extract with fuzzy matching for typos
- `GET /items-by-identifiers` - Fetch items from Qdrant by identifiers
- `POST /items-with-identifiers` - Add/update items in resources file

#### Ingest Routes (`/v1/api/analytics`)
- `POST /ingest` - Ingest estimator items into Qdrant database

#### Config Routes (`/v1/api/analytics`)
- `GET /config` - Get application configuration

#### Auth Routes (`/v1/api/analytics`)
- `GET /get-auth-token` - Fetch authentication token

#### Health Check
- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint

## Project Structure

```
backend/
├── routes/
│   ├── __init__.py
│   ├── controller.py          # Main app with router configuration
│   ├── items_routes.py        # Item management endpoints
│   ├── search_routes.py       # Search functionality endpoints
│   ├── ingest_routes.py       # Data ingestion endpoints
│   ├── config_routes.py       # Configuration endpoints
│   └── auth_routes.py         # Authentication endpoints
├── services/                  # Business logic layer
├── utils/                     # Helper functions and utilities
├── resources/                 # Static resources and data files
└── scripts/                   # Data enrichment scripts
```

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.10+

### Running with Docker

1. Update the shared key path in `docker-compose.yml` if needed
2. Start the services:
```bash
docker-compose up --build
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8090
- API Documentation: http://localhost:8090/docs
- Qdrant: http://localhost:6333

## Recent Changes

### v1.0.0 - Route Refactoring & API Versioning
- ✅ Organized routes into separate modules by functionality
- ✅ Added `/v1/api/analytics` prefix to all API endpoints
- ✅ Updated frontend to use new API prefix
- ✅ Fixed docker-compose.yml volume path for renamed folder
- ✅ Updated entrypoint.sh to reference new route structure
- ✅ Added comprehensive API documentation

## Features

- 🔍 Multilingual search (Hindi, Bengali, Tamil, Telugu, Kannada, Malayalam, English)
- 🎯 Fuzzy matching for handling typos
- 🗣️ Voice search support (browser-based)
- 💾 Qdrant vector database integration
- 📊 Price analytics and aggregated views
- 🌍 City-based filtering for pricing data
- 🔄 Data ingestion from external APIs
- 🐳 Dockerized deployment