# Pitchly — AI Project Planning Copilot

Welcome to **Pitchly**, an AI copilot that turns rough ideas into structured engineering roadmaps and interactive Kanban boards.

The complete MVP application is located in the [`pitchly/`](./pitchly/) directory.

## Quick Links
- **[Pitchly README & Architecture Documentation](./pitchly/README.md)**
- **[Docker Compose Setup](./pitchly/docker-compose.yml)**
- **[Backend (Django + DRF + Channels)](./pitchly/backend/)**
- **[Frontend (React + Vite + dnd-kit)](./pitchly/frontend/)**

To launch Pitchly immediately:
```bash
cd pitchly
docker compose up --build
```
Or run locally without Docker:
```bash
# Terminal 1: Backend
cd pitchly/backend
python manage.py migrate
daphne -b 127.0.0.1 -p 8000 pitchly_backend.asgi:application

# Terminal 2: Frontend
cd pitchly/frontend
npm run dev
```
Visit `http://localhost:5173` to get started!
