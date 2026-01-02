#!/bin/bash

BASE_URL="http://localhost:8000" # FastAPI server runs on port 8000

echo "=== FastAPI Backend cURL Commands ==="
echo ""

echo "--- GET / ---"
echo "Serves the main UI page (placeholder HTML)."
curl -X GET "${BASE_URL}/"
echo ""
echo ""

echo "--- GET /api/messages ---"
echo "Get messages with optional filters."
echo "Example: Get 2 messages, offset by 0, from 'MyChannel', searching for 'hello', between 2023-01-01 and 2023-12-31, and not trashed."
curl -X GET "${BASE_URL}/api/messages?limit=2&offset=0&channel=MyChannel&search=hello&start_date=2023-01-01&end_date=2023-12-31"
echo ""
echo "Example: Get all messages (default limit/offset), not trashed."
curl -X GET "${BASE_URL}/api/messages"
echo ""
echo ""

echo "--- GET /api/channels ---"
echo "Get list of channels with message counts and fetch status."
curl -X GET "${BASE_URL}/api/channels"
echo ""
echo ""

echo "--- GET /api/stats ---"
echo "Get database statistics."
curl -X GET "${BASE_URL}/api/stats"
echo ""
echo ""

echo "--- PUT /api/messages/{message_id}/read ---"
echo "Mark a message as read. (POST also supported)"
echo "Example: Mark message with ID 1 as read."
curl -X PUT "${BASE_URL}/api/messages/1/read"
echo ""
echo ""

echo "--- PUT /api/messages/{message_id}/like ---"
echo "Toggle like status of a message. (POST also supported)"
echo "Example: Toggle like status for message with ID 1."
curl -X PUT "${BASE_URL}/api/messages/1/like"
echo ""
echo ""

echo "--- PUT /api/messages/{message_id}/trash ---"
echo "Toggle trash status of a message. (POST also supported)"
echo "Example: Trash message with ID 1."
curl -X PUT "${BASE_URL}/api/messages/1/trash"
echo ""
echo "Example: Restore message with ID 1 (if trashed)."
curl -X PUT "${BASE_URL}/api/messages/1/trash"
echo ""
echo ""

echo "--- PUT /api/channels/{channel_name}/fetch-status ---"
echo "Update fetch status information for a channel. (POST also supported)"
echo "Example: Update fetch status for 'MyChannel'."
curl -X PUT "${BASE_URL}/api/channels/MyChannel/fetch-status" \
     -H "Content-Type: application/json" \
     -d '{ \
           "fetchstatus": "completed", \
           "fetchedStartedAt": "2023-01-01T10:00:00Z", \
           "fetchedEndedAt": "2023-01-01T10:30:00Z" \
         }'
echo ""
echo ""

echo "--- PUT /api/messages/{message_id}/tags ---"
echo "Update tags for a message. (POST also supported)"
echo "Example: Set tags for message with ID 1 to 'important,work'."
curl -X PUT "${BASE_URL}/api/messages/1/tags" \
     -H "Content-Type: application/json" \
     -d '{ \
           "tags": "important,work" \
         }'
echo ""
echo ""

echo "--- POST /api/scraper/start ---"
echo "Proxy endpoint to start Telegram scraping."
curl -X POST "${BASE_URL}/api/scraper/start" \
     -H "Content-Type: application/json" \
     -d '{}'
echo ""
echo ""

echo "--- GET /api/scraper/status ---"
echo "Proxy endpoint to get Telegram scraping status."
curl -X GET "${BASE_URL}/api/scraper/status"
echo ""
echo ""

echo "--- GET /api/scraper/stats ---"
echo "Proxy endpoint to get Telegram scraping statistics."
curl -X GET "${BASE_URL}/api/scraper/stats"
echo ""
echo ""

echo "--- GET /health ---"
echo "Health check endpoint that verifies database connectivity."
curl -X GET "${BASE_URL}/health"
echo ""
echo ""
