# TeliBelly - Telegram Messages Dashboard

A complete solution for browsing and analyzing collected Telegram messages with both a Vue.js frontend and a Python/Flask backend API.

## Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│   Vue.js Frontend   │◄────────┤  Vite Dev Server    │
│   (Port: 5173)      │         │  (with Proxy)       │
└─────────────────────┘         └─────────────────────┘
                                      │
                                      ▼ HTTP Proxy (/api/*)
                                ┌─────────────────────┐
                                │  Python API Server  │
                                │   (Port: 5000)      │
                                └─────────────────────┘
                                      │
                                      ▼ SQLite
                                ┌─────────────────────┐
                                │  Telegram Database  │
                                │ telegram_backup.db  │
                                └─────────────────────┘
```

## Project Structure

```
TeliBelly/
├── data/              # SQLite database with Telegram messages
├── migrations/        # Database migration scripts
├── server/            # Python/Flask API server
│   ├── api_server.py  # Main API server
│   ├── migrate.py     # Database migration runner
│   ├── requirements.txt
│   └── README.md
├── src/               # Vue.js frontend application
│   ├── assets/        # Static assets and global styles
│   ├── components/    # Reusable Vue components
│   ├── router/        # Vue Router configuration
│   ├── views/         # Page-level components
│   ├── App.vue        # Main app component
│   └── main.js        # Application entry point
├── templates/         # Jinja2 templates (for the original Flask-based UI)
├── public/            # Static files for Vue.js app
├── README.md          # This file
└── package.json       # Node.js dependencies
```

## Features

- View collected Telegram messages in a dashboard format
- Filter messages by channel, search terms, date range
- Mark messages as read/liked/trashed
- Tag messages for organization
- View statistics about messages and channels

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- Python 3.8+
- SQLite database with Telegram messages

### Installation

1. Install frontend dependencies:
   ```bash
   npm install
   ```

2. Install backend dependencies:
   ```bash
   pip install -r server/requirements.txt
   ```

### Running the Application

You can start both servers simultaneously using the provided script:

```bash
./start-servers.sh start
```

Or start them separately:

1. Start the Vue.js development server:
   ```bash
   npm run dev
   ```

2. In a separate terminal, start the Python API server:
   ```bash
   cd server
   python api_server.py
   ```

3. Open your browser to `http://localhost:5173` to view the dashboard with the Vue.js frontend communicating with the Python backend API through a proxy.

The Vue.js development server is configured with a proxy that forwards all `/api/*` requests to the Python API server running on `http://localhost:5000`, eliminating CORS issues during development.

## Database Migrations

To run database migrations:
```bash
cd server
python migrate.py up
```

To check migration status:
```bash
cd server
python migrate.py status
```

## Telegram Scraper API

This project now includes a separate API service for triggering Telegram scraping operations without modifying the existing `main.py` file:

1. Start both API services:
   ```bash
   ./server/start_servers.sh
   ```

2. Trigger scraping via the API:
   ```bash
   curl -X POST http://localhost:5000/api/scraper/start -H "Content-Type: application/json" -d '{"days_back": 3}'
   ```

3. Check scraping status:
   ```bash
   curl http://localhost:5000/api/scraper/status
   ```

See `server/README_TELEGRAM_SCRAPER_API.md` for complete API documentation.