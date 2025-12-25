#!/usr/bin/env python3
"""
API Server for Telegram Messages
Provides RESTful endpoints to access messages from SQLite database
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from flask import Flask, jsonify, request, render_template_string, render_template
from flask_cors import CORS
from flask import render_template

HTML_TEMPLATE = "index.html.jinja"

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database path
DB_PATH = "data/telegram_backup.db"

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def init_db():
    """Initialize database connection and check if tables exist"""
    try:
        with get_db_connection() as conn:
            # Test connection by querying tables
            conn.execute("SELECT 1 FROM messages LIMIT 1")
            conn.execute("SELECT 1 FROM channels LIMIT 1")
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

@app.route('/')
def index():
    """Serve the main UI page"""
    return render_template("index.html")

@app.route('/api/messages')
def get_messages():
    """Get messages with optional filters"""
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        channel = request.args.get('channel', '')
        search = request.args.get('search', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        filter_read = request.args.get('filter_read', '')
        filter_like = request.args.get('filter_like', '')
        filter_trash = request.args.get('filter_trash', '')
        
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
        with get_db_connection() as conn:
            messages = conn.execute(query, params).fetchall()
            
        # Convert to dict
        result = [dict(msg) for msg in messages]
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/channels')
def get_channels():
    """Get list of channels with message counts"""
    try:
        query = """
            SELECT c.channel_name, c.total_messages, c.last_backup_timestamp
            FROM channels c
            ORDER BY c.total_messages DESC
        """
        
        with get_db_connection() as conn:
            channels = conn.execute(query).fetchall()
            
        # Convert to dict
        result = [dict(channel) for channel in channels]
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    try:
        with get_db_connection() as conn:
            # Total messages
            total_messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            
            # Total channels
            total_channels = conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
            
            # Date range
            date_range = conn.execute("""
                SELECT 
                    MIN(datetime_local) as earliest,
                    MAX(datetime_local) as latest
                FROM messages
            """).fetchone()
            
        return jsonify({
            'success': True,
            'data': {
                'total_messages': total_messages,
                'total_channels': total_channels,
                'date_range': {
                    'earliest': date_range['earliest'],
                    'latest': date_range['latest']
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/messages/<int:message_id>/read', methods=['PUT', 'POST'])
def mark_message_read(message_id):
    """Mark a message as read"""
    try:
        with get_db_connection() as conn:
            conn.execute("UPDATE messages SET read = 1 WHERE id = ?", (message_id,))
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Message marked as read'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/messages/<int:message_id>/like', methods=['PUT', 'POST'])
def toggle_message_like(message_id):
    """Toggle like status of a message"""
    try:
        with get_db_connection() as conn:
            # Get current like status
            current = conn.execute("SELECT like FROM messages WHERE id = ?", (message_id,)).fetchone()
            
            if not current:
                return jsonify({
                    'success': False,
                    'error': 'Message not found'
                }), 404
            
            new_status = 1 - current[0]  # Toggle between 0 and 1
            conn.execute("UPDATE messages SET like = ? WHERE id = ?", (new_status, message_id))
            conn.commit()
        
        return jsonify({
            'success': True,
            'liked': bool(new_status),
            'message': 'Like status updated'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/messages/<int:message_id>/trash', methods=['PUT', 'POST'])
def toggle_message_trash(message_id):
    """Toggle trash status of a message"""
    try:
        with get_db_connection() as conn:
            # Get current trash status
            current = conn.execute("SELECT trashed_at FROM messages WHERE id = ?", (message_id,)).fetchone()
            
            if not current:
                return jsonify({
                    'success': False,
                    'error': 'Message not found'
                }), 404
            
            # If trashed_at is NULL, set it to current timestamp, otherwise set to NULL
            if current[0] is None:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                conn.execute("UPDATE messages SET trashed_at = ? WHERE id = ?", (timestamp, message_id))
                action = 'trashed'
            else:
                conn.execute("UPDATE messages SET trashed_at = NULL WHERE id = ?", (message_id,))
                action = 'restored'
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'action': action,
            'message': f'Message {action}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/messages/<int:message_id>/tags', methods=['PUT', 'POST'])
def update_message_tags(message_id):
    """Update tags for a message"""
    try:
        # Get tags from request
        data = request.get_json()
        new_tags = data.get('tags', '')

        # Validate tags format (comma-separated string)
        if not isinstance(new_tags, str):
            return jsonify({
                'success': False,
                'error': 'Tags must be a comma-separated string'
            }), 400

        with get_db_connection() as conn:
            # Check if message exists
            message = conn.execute("SELECT id, tags FROM messages WHERE id = ?", (message_id,)).fetchone()

            if not message:
                return jsonify({
                    'success': False,
                    'error': 'Message not found'
                }), 404

            # Update tags in messages table
            conn.execute("UPDATE messages SET tags = ? WHERE id = ?", (new_tags, message_id))

            # Get current tags for the message
            old_tags = message['tags'] if message['tags'] else ''
            old_tag_list = [tag.strip() for tag in old_tags.split(',') if tag.strip()]
            new_tag_list = [tag.strip() for tag in new_tags.split(',') if tag.strip()]

            # Update tags table
            # Remove message from old tags
            for tag_name in old_tag_list:
                tag_record = conn.execute("SELECT id, message_ids FROM tags WHERE name = ?", (tag_name,)).fetchone()
                if tag_record:
                    message_ids = tag_record['message_ids'] if tag_record['message_ids'] else ''
                    message_id_list = [mid.strip() for mid in message_ids.split(',') if mid.strip()]

                    # Remove this message ID from the list
                    if str(message_id) in message_id_list:
                        message_id_list.remove(str(message_id))
                        updated_message_ids = ','.join(message_id_list) if message_id_list else None

                        if updated_message_ids:
                            conn.execute("UPDATE tags SET message_ids = ? WHERE name = ?", (updated_message_ids, tag_name))
                        else:
                            # If no messages left with this tag, delete the tag
                            conn.execute("DELETE FROM tags WHERE name = ?", (tag_name,))

            # Add message to new tags
            for tag_name in new_tag_list:
                if tag_name:  # Only process non-empty tags
                    tag_record = conn.execute("SELECT id, message_ids FROM tags WHERE name = ?", (tag_name,)).fetchone()
                    if tag_record:
                        # Tag exists, update message_ids
                        message_ids = tag_record['message_ids'] if tag_record['message_ids'] else ''
                        message_id_list = [mid.strip() for mid in message_ids.split(',') if mid.strip()]

                        # Add this message ID to the list if not already present
                        if str(message_id) not in message_id_list:
                            message_id_list.append(str(message_id))
                            updated_message_ids = ','.join(message_id_list)
                            conn.execute("UPDATE tags SET message_ids = ? WHERE name = ?", (updated_message_ids, tag_name))
                    else:
                        # Tag doesn't exist, create it
                        conn.execute("INSERT INTO tags (name, message_ids) VALUES (?, ?)", (tag_name, str(message_id)))

            conn.commit()

        return jsonify({
            'success': True,
            'message': 'Tags updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize database
    if not init_db():
        print("Failed to initialize database. Exiting.")
        exit(1)
    
    # Run the server
    print("🚀 Starting Telegram Messages Dashboard...")
    print("📍 Visit http://localhost:5000 to view the dashboard")
    app.run(host='0.0.0.0', port=5000, debug=True)
