# Logistics POC

A proof-of-concept logistics application with FastAPI backend and React frontend.

## Quick start

```bash
# Start infrastructure (if Docker is available)
cd infra && docker compose up -d

# Start backend API
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8001

# Start frontend
cd frontend && npm install && npm run dev
```

## Architecture

- **Backend**: FastAPI with Python 3.11+
- **Frontend**: React + TypeScript + Vite + MapLibre GL
- **Database**: PostgreSQL (via Docker)
- **Cache**: Redis (via Docker)

## API Endpoints

- `GET /health` - Health check
- `GET /warehouses` - List of warehouse locations

## Development

The application includes:
- Interactive map showing warehouse locations
- REST API with warehouse data
- Hot reload for both backend and frontend
- VS Code configuration and extensions