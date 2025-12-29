#!/usr/bin/env python3
"""
Telegram Scraper API - Provides endpoints to trigger scraping operations
without modifying the existing main.py file
"""

import asyncio
import threading
import json
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

# Import the core Telegram functionality
from telegram_auth import TelegramAuth
from telegram_fetch import MessageFetcher
from telegram_master_xlsx import TelegramMasterXLSX
from sqlite_backup import SQLiteBackup

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variable to track scraping status
scraping_status = {
    "is_running": False,
    "start_time": None,
    "progress": "",
    "channels_processed": 0,
    "total_channels": 0,
    "messages_added": 0,
    "current_channel": None
}

# Database and output paths (should match main.py)
OUTPUT_DIRECTORY = "../data"
MASTER_FILE_PATH = OUTPUT_DIRECTORY + "/telegram_messages_master.xlsx"
DB_PATH = OUTPUT_DIRECTORY + "/telegram_backup.db"

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def update_channel_fetch_status(channel_name, fetchstatus=None, fetchedStartedAt=None, fetchedEndedAt=None):
    """Update fetch status information for a channel"""
    try:
        with get_db_connection() as conn:
            # Check if channel exists
            channel = conn.execute("SELECT id FROM channels WHERE channel_name = ?", (channel_name,)).fetchone()

            if not channel:
                # Create channel if it doesn't exist
                conn.execute("""
                    INSERT INTO channels (channel_name, last_backup_timestamp)
                    VALUES (?, ?)
                """, (channel_name, datetime.now().isoformat()))
            
            # Update fetch status fields
            update_fields = []
            update_params = []

            if fetchstatus is not None:
                update_fields.append("fetchstatus = ?")
                update_params.append(fetchstatus)

            if fetchedStartedAt is not None:
                update_fields.append("fetchedStartedAt = ?")
                update_params.append(fetchedStartedAt)

            if fetchedEndedAt is not None:
                update_fields.append("fetchedEndedAt = ?")
                update_params.append(fetchedEndedAt)

            # Always update the timestamp
            update_fields.append("last_backup_timestamp = ?")
            update_params.append(datetime.now().isoformat())
            update_params.append(channel_name)

            if update_fields:
                query = f"UPDATE channels SET {', '.join(update_fields)} WHERE channel_name = ?"
                conn.execute(query, update_params)
                conn.commit()

        return True
    except Exception as e:
        print(f"Error updating channel fetch status: {e}")
        return False

def run_async_task(coro):
    """Helper function to run async tasks in a separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

async def scrape_telegram_async(days_back=3, limit=1000):
    """Async function to perform Telegram scraping"""
    global scraping_status

    try:
        # Update status
        scraping_status["is_running"] = True
        scraping_status["start_time"] = datetime.now().isoformat()
        scraping_status["progress"] = "Initializing..."
        scraping_status["channels_processed"] = 0
        scraping_status["messages_added"] = 0

        # Initialize components
        scraping_status["progress"] = "Initializing authentication..."
        auth = TelegramAuth()
        master = TelegramMasterXLSX(MASTER_FILE_PATH, DB_PATH)
        sqlite_backup = SQLiteBackup(DB_PATH)

        # Connect to Telegram
        scraping_status["progress"] = "Connecting to Telegram..."
        connected = await auth.connect()
        if not connected:
            scraping_status["progress"] = "Failed to connect to Telegram"
            return {"success": False, "error": "Failed to connect to Telegram"}

        # Get channels
        scraping_status["progress"] = "Discovering channels..."
        channels_data = await auth.get_channels(limit=limit)
        if not channels_data:
            scraping_status["progress"] = "No channels found"
            await auth.disconnect()
            return {"success": False, "error": "No channels found"}

        scraping_status["total_channels"] = len(channels_data)

        # Initialize fetcher
        fetcher = MessageFetcher(auth.client)

        # Process channels
        scraping_status["progress"] = "Processing channels..."
        total_new_messages = 0
        processed_channels = 0

        for i, channel in enumerate(channels_data, 1):
            channel_name = channel['name']
            scraping_status["current_channel"] = channel_name
            
            # Update channel fetch status to processing when starting
            update_channel_fetch_status(
                channel_name,
                fetchstatus="processing",
                fetchedStartedAt=datetime.now().isoformat(),
                fetchedEndedAt=None
            )

            scraping_status["progress"] = f"Processing channel [{i}/{len(channels_data)}] {channel_name}"
            scraping_status["channels_processed"] = i

            # Fetch messages
            messages = await fetcher.fetch_messages(
                channel["dialog"], days_back=days_back, limit=limit
            )

            if messages:
                # Format messages for storage
                formatted_messages = []
                for msg in messages:
                    formatted_messages.append({
                        "channel_id": channel["id"],
                        "channel_name": channel_name,
                        "message_id": msg["message"].id,
                        "global_id": msg.get("global_id"),
                        "datetime_utc": msg["datetime_utc"],
                        "datetime_local": msg["datetime_local"],
                        "sender_id": msg["sender_id"],
                        "sender_name": msg["sender_name"],
                        "text": msg["text"],
                        "media_type": msg["media_type"],
                        "views": msg["views"],
                        "forwards": msg["forwards"],
                    })

                # Add to master - translation happens here!
                new_count = master.add_messages(formatted_messages, channel_name)

                # Backup to SQLite
                if new_count > 0:
                    sqlite_backup.backup_messages(formatted_messages, channel_name)

                total_new_messages += new_count
                processed_channels += 1

                # Update status with progress
                scraping_status["messages_added"] = total_new_messages

            # Update channel fetch status to done when completed
            update_channel_fetch_status(
                channel_name,
                fetchstatus="done",
                fetchedEndedAt=datetime.now().isoformat()
            )

        # Finalize
        scraping_status["progress"] = "Finalizing..."
        await auth.disconnect()

        # Update final status
        scraping_status["is_running"] = False
        scraping_status["progress"] = "Completed"
        scraping_status["current_channel"] = None

        return {
            "success": True,
            "channels_processed": len(channels_data),
            "channels_with_new_messages": processed_channels,
            "new_messages_added": total_new_messages
        }

    except Exception as e:
        # If there's an error and we're processing a channel, mark it as failed
        if scraping_status.get("current_channel"):
            update_channel_fetch_status(
                scraping_status["current_channel"],
                fetchstatus="failed",
                fetchedEndedAt=datetime.now().isoformat()
            )
        
        scraping_status["is_running"] = False
        scraping_status["progress"] = f"Error: {str(e)}"
        scraping_status["current_channel"] = None
        return {"success": False, "error": str(e)}

def scrape_telegram_background(days_back=3, limit=1000):
    """Function to run the scraper in a background thread"""
    result = run_async_task(scrape_telegram_async(days_back, limit))
    return result

@app.route('/api/scrape/start', methods=['POST'])
def start_scraping():
    """Start the Telegram scraping process"""
    global scraping_status

    if scraping_status["is_running"]:
        return jsonify({
            "success": False,
            "error": "Scraping is already in progress"
        }), 400

    # Get parameters from request
    data = request.get_json() or {}
    days_back = data.get('days_back', 3)
    limit = data.get('limit', 1000)

    # Validate parameters
    if not isinstance(days_back, int) or days_back <= 0:
        return jsonify({
            "success": False,
            "error": "days_back must be a positive integer"
        }), 400

    if not isinstance(limit, int) or limit <= 0:
        return jsonify({
            "success": False,
            "error": "limit must be a positive integer"
        }), 400

    # Start scraping in a background thread
    thread = threading.Thread(
        target=scrape_telegram_background,
        kwargs={'days_back': days_back, 'limit': limit}
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        "success": True,
        "message": "Scraping started",
        "estimated_duration": "Several minutes depending on the number of channels and messages"
    })

@app.route('/api/scrape/status', methods=['GET'])
def get_scraping_status():
    """Get the current status of the scraping process"""
    return jsonify({
        "success": True,
        "status": scraping_status
    })

@app.route('/api/scrape/stats', methods=['GET'])
def get_scraping_stats():
    """Get statistics about the data"""
    try:
        # Initialize components to get stats
        master = TelegramMasterXLSX(MASTER_FILE_PATH, DB_PATH)
        sqlite_backup = SQLiteBackup(DB_PATH)

        stats_before = master.get_stats()
        backup_stats = sqlite_backup.get_backup_stats()

        return jsonify({
            "success": True,
            "master_stats": stats_before,
            "backup_stats": backup_stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Telegram Scraper API...")
    print("📍 Visit http://localhost:5001 to access the API")
    app.run(host='0.0.0.0', port=5001, debug=True)