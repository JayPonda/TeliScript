import logging
logging.basicConfig(level=logging.INFO)
import sqlite3
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


from fastapi import FastAPI, HTTPException, status, Depends, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import the core Telegram functionality
import asyncio
import threading
from telegram_auth import TelegramAuth
from telegram_fetch import MessageFetcher
from telegram_master_xlsx import TelegramMasterXLSX
from sqlite_backup import SQLiteBackup

from pydantic import ValidationError

# Import models
from models import MessageBase, ChannelBase, ApiResponse, MessagesResponse, ChannelsResponse, StatsResponse, MessageTagsUpdate, ChannelFetchStatusUpdate, ScraperStartRequest

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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

# Database and output paths
OUTPUT_DIRECTORY = "data"
MASTER_FILE_PATH = OUTPUT_DIRECTORY + "/telegram_messages_master.xlsx"
DB_PATH = OUTPUT_DIRECTORY + "/telegram_backup.db"


def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize database connection and check if tables exist"""
    try:
        # Use a temporary connection for initialization
        temp_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        temp_conn.row_factory = sqlite3.Row
        with temp_conn as conn:
            # Test connection by querying tables
            conn.execute("SELECT 1 FROM messages LIMIT 1")
            conn.execute("SELECT 1 FROM channels LIMIT 1")
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main UI page"""
    # In a real FastAPI app, you would typically serve static files
    # or use a templating engine like Jinja2. For simplicity,
    # assuming index.html is directly served or built by the frontend.
    # We will need to make sure the frontend build is served by FastAPI or Nginx
    # For now, a placeholder.
    return "<h1>Telegram Messages Dashboard (FastAPI)</h1><p>Frontend will be served here.</p>"

@app.get("/api/messages", response_model=MessagesResponse)
async def get_messages(
    limit: int = 50,
    offset: int = 0,
    channel: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    filter_read: bool = False,
    filter_like: bool = False,
    filter_trash: bool = False,
    db: sqlite3.Connection = Depends(get_db_connection)
):
    """Get messages with optional filters"""
    try:
        # Build query
        query = """
            SELECT id, channel_name, text_translated, datetime_local, sender_name, views, forwards, media_type, like, read, trashed_at, tags
            FROM messages
            WHERE 1=1
        """
        params = []
        
        # Channel filter
        if channel:
            query += " AND channel_name = ?"
            params.append(channel)
            
        # Search filter (in text or sender name)
        if search:
            query += " AND (text_translated LIKE ? OR sender_name LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
            
        # Date range filter
        if start_date:
            query += " AND datetime_local >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND datetime_local <= ?"
            params.append(end_date)
        
        # Read filter
        if filter_read:
            query += " AND read = 1"
        
        # Like filter
        if filter_like:
            query += " AND like = 1"
            
        # Trash filter
        if filter_trash:
            query += " AND trashed_at IS NOT NULL"
        else:
            # By default, don't show trashed messages
            query += " AND trashed_at IS NULL"
            
        # Order and limit
        query += " ORDER BY datetime_local DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute query
        messages = db.execute(query, params).fetchall()
            
        # Convert to dict
        result = [dict(msg) for msg in messages]

        return MessagesResponse(
            success=True,
            data=[MessageBase(**msg) for msg in result],
            count=len(result)
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/channels", response_model=ChannelsResponse)
async def get_channels(db: sqlite3.Connection = Depends(get_db_connection)):
    """Get list of channels with message counts and fetch status"""
    try:
        query = """
            SELECT 
                id,
                channel_id,
                channel_name,
                total_messages,
                last_backup_timestamp,
                fetchstatus,
                fetchedStartedAt,
                fetchedEndedAt
            FROM channels
            ORDER BY total_messages DESC
        """

        channels = db.execute(query).fetchall()

        # Convert to dict
        result = []
        for channel in channels:
            channel_dict = dict(channel)

            # Convert all integer IDs to strings to match the Pydantic model
            if "id" in channel_dict:
                channel_dict["id"] = (
                    str(channel_dict["id"]) if channel_dict["id"] is not None else None
                )

            # Convert channel_id to string if it exists
            if "channel_id" in channel_dict:
                channel_dict["channel_id"] = (
                    str(channel_dict["channel_id"])
                    if channel_dict["channel_id"] is not None
                    else None
                )

            result.append(channel_dict)

        logging.info(f"Found {len(result)} channels")
        logging.info(
            f"First channel data (after conversion): {result[0] if result else 'No data'}"
        )

        # Create ChannelBase instances
        channel_objects = []
        for row in result:
            logging.info(f"Attempting to create ChannelBase from row: {row}") # ADDED LOGGING HERE
            try:
                channel_obj = ChannelBase(
                    id=row.get("id"),  # This is now a string
                    channel_id=row.get("channel_id"),
                    channel_name=row.get("channel_name", "Unknown"),
                    total_messages=row.get("total_messages", 0),
                    last_backup_timestamp=row.get("last_backup_timestamp"),
                    fetchstatus=row.get("fetchstatus"),
                    fetchedStartedAt=row.get("fetchedStartedAt"),
                    fetchedEndedAt=row.get("fetchedEndedAt"),
                )
                channel_objects.append(channel_obj)
            except Exception as e:
                logging.error(f"Error parsing channel row {row}: {e}", exc_info=True)
                continue

        return ChannelsResponse(
            success=True, data=channel_objects, count=len(channel_objects)
        )

    except Exception as e:
        logging.error(f"Error in get_channels: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

@app.post("/api/debug/validate_channel")
async def debug_validate_channel(request: Request):
    """
    Receives any JSON body, prints it, and then attempts to validate it 
    against the ChannelBase model. This helps in debugging validation issues.
    """
    # 1. Get the raw JSON data from the request body
    try:
        raw_data = await request.json()
        logging.info("--- Received Raw Data ---")
        logging.info(raw_data)
        logging.info("-------------------------")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse JSON body: {e}")

    # 2. Manually attempt to validate the data using your Pydantic model
    try:
        # We pass the raw_data dictionary to the ChannelBase model
        validated_data = ChannelBase(**raw_data)
        
        logging.info("--- Validation Successful ---")
        logging.info(validated_data)
        logging.info("---------------------------")
        
        return {
            "status": "Validation Successful",
            "raw_data_received": raw_data,
            "data_after_validation": validated_data.dict()
        }

    except ValidationError as e:
        # 3. If validation fails, return the raw data and the specific errors
        logging.info("--- Validation Failed ---")
        # .errors() gives a clean list of validation problems
        logging.info(e.errors())
        logging.info("-------------------------")
        
        return JSONResponse(
            status_code=422,
            content={
                "status": "Validation Failed",
                "raw_data_received": raw_data,
                "validation_errors": e.errors(),
            }
        )

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: sqlite3.Connection = Depends(get_db_connection)):
    """Get database statistics"""
    try:
        # Total messages
        total_messages = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        
        # Total channels
        total_channels = db.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
        
        # Date range
        date_range = db.execute("""
            SELECT 
                MIN(datetime_local) as earliest,
                MAX(datetime_local) as latest
            FROM messages
        """).fetchone()
        
        return StatsResponse(
            success=True,
            data={
                'total_messages': total_messages,
                'total_channels': total_channels,
                'date_range': {
                    'earliest': date_range['earliest'],
                    'latest': date_range['latest']
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.put("/api/messages/{message_id}/read", response_model=ApiResponse)
@app.post("/api/messages/{message_id}/read", response_model=ApiResponse)
async def mark_message_read(message_id: int, db: sqlite3.Connection = Depends(get_db_connection)):
    """Mark a message as read"""
    try:
        db.execute("UPDATE messages SET read = 1 WHERE id = ?", (message_id,))
        db.commit()
        
        return ApiResponse(
            success=True,
            message='Message marked as read'
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.put("/api/messages/{message_id}/like", response_model=ApiResponse)
@app.post("/api/messages/{message_id}/like", response_model=ApiResponse)
async def toggle_message_like(message_id: int, db: sqlite3.Connection = Depends(get_db_connection)):
    """Toggle like status of a message"""
    try:
        # Get current like status
        current = db.execute("SELECT like FROM messages WHERE id = ?", (message_id,)).fetchone()
        
        if not current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Message not found')
        
        new_status = 1 - current[0]  # Toggle between 0 and 1
        db.execute("UPDATE messages SET like = ? WHERE id = ?", (new_status, message_id))
        db.commit()
        
        return ApiResponse(
            success=True,
            data={'liked': bool(new_status)},
            message='Like status updated'
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.put("/api/messages/{message_id}/trash", response_model=ApiResponse)
@app.post("/api/messages/{message_id}/trash", response_model=ApiResponse)
async def toggle_message_trash(message_id: int, db: sqlite3.Connection = Depends(get_db_connection)):
    """Toggle trash status of a message"""
    try:
        # Get current trash status
        current = db.execute("SELECT trashed_at FROM messages WHERE id = ?", (message_id,)).fetchone()
        
        if not current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Message not found')
        
        # If trashed_at is NULL, set it to current timestamp, otherwise set to NULL
        if current[0] is None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.execute("UPDATE messages SET trashed_at = ? WHERE id = ?", (timestamp, message_id))
            action = 'trashed'
        else:
            db.execute("UPDATE messages SET trashed_at = NULL WHERE id = ?", (message_id,))
            action = 'restored'
        
        db.commit()
        
        return ApiResponse(
            success=True,
            data={'action': action},
            message=f'Message {action}'
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.put("/api/channels/{channel_name}/fetch-status", response_model=ApiResponse)
@app.post("/api/channels/{channel_name}/fetch-status", response_model=ApiResponse)
async def update_channel_fetch_status(
    channel_name: str, 
    data: ChannelFetchStatusUpdate, 
    db: sqlite3.Connection = Depends(get_db_connection)
):
    """Update fetch status information for a channel"""
    try:
        # Check if channel exists
        channel = db.execute("SELECT id FROM channels WHERE channel_name = ?", (channel_name,)).fetchone()

        if not channel:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Channel not found')

        # Update fetch status fields
        update_fields = []
        update_params = []

        if data.fetchstatus is not None:
            update_fields.append("fetchstatus = ?")
            update_params.append(data.fetchstatus)

        if data.fetchedStartedAt is not None:
            update_fields.append("fetchedStartedAt = ?")
            update_params.append(data.fetchedStartedAt)

        if data.fetchedEndedAt is not None:
            update_fields.append("fetchedEndedAt = ?")
            update_params.append(data.fetchedEndedAt)

        # Always update the timestamp
        update_fields.append("last_backup_timestamp = ?")
        update_params.append(datetime.now().isoformat())
        update_params.append(channel_name)

        if update_fields:
            query = f"UPDATE channels SET {', '.join(update_fields)} WHERE channel_name = ?"
            db.execute(query, update_params)
            db.commit()

        return ApiResponse(
            success=True,
            message='Channel fetch status updated successfully'
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.put("/api/messages/{message_id}/tags", response_model=ApiResponse)
@app.post("/api/messages/{message_id}/tags", response_model=ApiResponse)
async def update_message_tags(
    message_id: int, 
    tags_update: MessageTagsUpdate, 
    db: sqlite3.Connection = Depends(get_db_connection)
):
    """Update tags for a message"""
    try:
        new_tags = tags_update.tags

        # Validate tags format (comma-separated string)
        if not isinstance(new_tags, str):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Tags must be a comma-separated string')

        # Check if message exists
        message = db.execute("SELECT id, tags FROM messages WHERE id = ?", (message_id,)).fetchone()

        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Message not found')

        # Update tags in messages table
        db.execute("UPDATE messages SET tags = ? WHERE id = ?", (new_tags, message_id))

        # Get current tags for the message
        old_tags = message['tags'] if message['tags'] else ''
        old_tag_list = [tag.strip() for tag in old_tags.split(',') if tag.strip()]
        new_tag_list = [tag.strip() for tag in new_tags.split(',') if tag.strip()]

        # Update tags table
        # Remove message from old tags
        for tag_name in old_tag_list:
            tag_record = db.execute("SELECT id, message_ids FROM tags WHERE name = ?", (tag_name,)).fetchone()
            if tag_record:
                message_ids = tag_record['message_ids'] if tag_record['message_ids'] else ''
                message_id_list = [mid.strip() for mid in message_ids.split(',') if mid.strip()]

                # Remove this message ID from the list
                if str(message_id) in message_id_list:
                    message_id_list.remove(str(message_id))
                    updated_message_ids = ','.join(message_id_list) if message_id_list else None

                    if updated_message_ids:
                        db.execute("UPDATE tags SET message_ids = ? WHERE name = ?", (updated_message_ids, tag_name))
                    else:
                        # If no messages left with this tag, delete the tag
                        db.execute("DELETE FROM tags WHERE name = ?", (tag_name,))

        # Add message to new tags
        for tag_name in new_tag_list:
            if tag_name:  # Only process non-empty tags
                tag_record = db.execute("SELECT id, message_ids FROM tags WHERE name = ?", (tag_name,)).fetchone()
                if tag_record:
                    # Tag exists, update message_ids
                    message_ids = tag_record['message_ids'] if tag_record['message_ids'] else ''
                    message_id_list = [mid.strip() for mid in message_ids.split(',') if mid.strip()]

                    # Add this message ID to the list if not already present
                    if str(message_id) not in message_id_list:
                        message_id_list.append(str(message_id))
                        updated_message_ids = ','.join(message_id_list)
                        db.execute("UPDATE tags SET message_ids = ? WHERE name = ?", (updated_message_ids, tag_name))
                else:
                    # Tag doesn't exist, create it
                    db.execute("INSERT INTO tags (name, message_ids) VALUES (?, ?)", (tag_name, str(message_id)))

        db.commit()

        return ApiResponse(
            success=True,
            message='Tags updated successfully'
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def _update_channel_fetch_status(channel_name, fetchstatus=None, fetchedStartedAt=None, fetchedEndedAt=None):
    """Update fetch status information for a channel"""
    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row
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
            _update_channel_fetch_status(
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
            _update_channel_fetch_status(
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
            _update_channel_fetch_status(
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

@app.post("/api/scraper/start", response_model=ApiResponse)
async def start_telegram_scraper(background_tasks: BackgroundTasks, data: ScraperStartRequest):
    """Start the Telegram scraping process"""
    global scraping_status

    if scraping_status["is_running"]:
        return ApiResponse(
            success=False,
            error="Scraping is already in progress"
        )

    # Get parameters from request
    days_back = data.days_back
    limit = data.limit

    # Validate parameters
    if not isinstance(days_back, int) or days_back <= 0:
        return ApiResponse(
            success=False,
            error="days_back must be a positive integer"
        )

    if not isinstance(limit, int) or limit <= 0:
        return ApiResponse(
            success=False,
            error="limit must be a positive integer"
        )

    # Start scraping in a background thread
    background_tasks.add_task(scrape_telegram_background, days_back=days_back, limit=limit)

    return ApiResponse(
        success=True,
        message="Scraping started",
        data={
            "estimated_duration": "Several minutes depending on the number of channels and messages"
        }
    )

    # """Proxy endpoint to get Telegram scraping status"""
    # response = None
    # try:
    #     # Forward the request to the telegram scraper API
    #     # scraper_url = f"{SCRAPER_URL_BASE}/status" # SCRAPER_URL_BASE is not defined
    #     # response = requests.get(scraper_url)
    #     # response.raise_for_status() # Raise an exception for HTTP errors
    #     # return JSONResponse(content=response.json(), status_code=response.status_code)
    # except requests.exceptions.ConnectionError:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail='Could not connect to Telegram scraper service. Please ensure it is running on port 5001.'
    #     )
    # except requests.exceptions.RequestException as e:
    #     raise HTTPException(
    #         status_code=response.status_code if response else status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f'Error communicating with scraper service: {str(e)}'
    #     )
    # except Exception as e:
    #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/api/scraper/stats", response_model=ApiResponse)
async def get_telegram_scraper_stats():
    """Get statistics about the data"""
    try:
        # Initialize components to get stats
        master = TelegramMasterXLSX(MASTER_FILE_PATH, DB_PATH)
        sqlite_backup = SQLiteBackup(DB_PATH)

        stats_before = master.get_stats()
        backup_stats = sqlite_backup.get_backup_stats()

        return ApiResponse(
            success=True,
            data={
                "master_stats": stats_before,
                "backup_stats": backup_stats
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )


@app.get("/api/health", response_model=ApiResponse)
async def health_check(db: sqlite3.Connection = Depends(get_db_connection)):
    """Health check endpoint that verifies database connectivity"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        return ApiResponse(
            success=True,
            data={
                'status': 'healthy',
                'database': 'connected',
                'next_check_in_seconds': 60
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            data={
                'status': 'unhealthy',
                'database': f'connection failed: {str(e)}',
                'next_check_in_seconds': 1
            }
        )

if __name__ == '__main__':
    # Initialize database
    if not init_db():
        print("Failed to initialize database. Exiting.")
        exit(1)
    
    # Run the server with uvicorn
    print("🚀 Starting Telegram Messages Dashboard (FastAPI)...")
    print("📍 Visit http://localhost:8000 to view the API documentation (Swagger UI)")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
