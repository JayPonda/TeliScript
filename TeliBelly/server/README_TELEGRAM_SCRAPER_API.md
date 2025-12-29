# Telegram Scraper API

This API provides endpoints to trigger Telegram scraping operations without modifying the existing `main.py` file.

## Endpoints

### Start Scraping
```
POST /api/scraper/start
```

Starts the Telegram scraping process. Accepts optional parameters:

- `days_back` (integer): Number of days back to fetch messages (default: 3)
- `limit` (integer): Maximum number of messages per channel (default: 1000)

Example request:
```json
{
  "days_back": 7,
  "limit": 500
}
```

### Get Scraping Status
```
GET /api/scraper/status
```

Returns the current status of the scraping process, including:
- Whether scraping is running
- Progress information
- Number of channels processed
- Number of messages added

### Get Statistics
```
GET /api/scraper/stats
```

Returns statistics about the stored data, including:
- Master file statistics
- SQLite backup statistics

## Usage

1. Start the main API server (runs on port 5000):
   ```
   python api_server.py
   ```

2. Start the Telegram scraper API (runs on port 5001):
   ```
   python telegram_scraper_api.py
   ```

3. Trigger scraping via the main API:
   ```
   curl -X POST http://localhost:5000/api/scraper/start -H "Content-Type: application/json" -d '{"days_back": 3}'
   ```

4. Check scraping status:
   ```
   curl http://localhost:5000/api/scraper/status
   ```

5. Get data statistics:
   ```
   curl http://localhost:5000/api/scraper/stats
   ```

## Response Format

All endpoints return JSON with a consistent format:
```json
{
  "success": true,
  "data": {...}
}
```

Or in case of errors:
```json
{
  "success": false,
  "error": "Error message"
}
```