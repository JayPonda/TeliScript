# Telegram Messages API Server

This is a Flask-based API server that provides RESTful endpoints to access Telegram messages stored in a SQLite database.

## Dependencies

- Python 3.8+
- Flask
- Flask-CORS

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
python api_server.py
```

The server will start on `http://localhost:5000`.

When used with the Vue.js frontend (which runs on `http://localhost:5173`), the frontend's development server is configured with a proxy that forwards all `/api/*` requests to this server, eliminating CORS issues during development.

## API Endpoints

- `GET /api/messages` - Get messages with optional filters
- `GET /api/channels` - Get list of channels with message counts
- `GET /api/stats` - Get database statistics
- `POST /api/messages/<id>/read` - Mark a message as read
- `POST /api/messages/<id>/like` - Toggle like status of a message
- `POST /api/messages/<id>/trash` - Toggle trash status of a message
- `POST /api/messages/<id>/tags` - Update tags for a message

## Database

The server expects a SQLite database file at `data/telegram_backup.db` with the following tables:
- `messages` - Contains the Telegram messages
- `channels` - Contains channel information
- `tags` - Contains tag information