"""
Pydantic models for Telegram Messages API
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class MessageBase(BaseModel):
    """Base model for message data"""
    id: int
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    message_id: Optional[str] = None
    global_id: Optional[str] = None
    datetime_utc: Optional[str] = None
    datetime_local: Optional[str] = None
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    text: Optional[str] = None
    text_translated: Optional[str] = None
    links: Optional[str] = None
    media_type: Optional[str] = None
    views: Optional[int] = None
    forwards: Optional[int] = None
    message_hash: Optional[str] = None
    added_at: Optional[str] = None
    backup_timestamp: Optional[str] = None
    like: Optional[bool] = False
    read: Optional[bool] = False
    trashed_at: Optional[str] = None
    tags: Optional[str] = None


class MessageCreate(BaseModel):
    """Model for creating a message"""
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    message_id: Optional[str] = None
    global_id: Optional[str] = None
    datetime_utc: Optional[str] = None
    datetime_local: Optional[str] = None
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    text: Optional[str] = None
    text_translated: Optional[str] = None
    links: Optional[str] = None
    media_type: Optional[str] = None
    views: Optional[int] = None
    forwards: Optional[int] = None
    message_hash: Optional[str] = None
    added_at: Optional[str] = None
    backup_timestamp: Optional[str] = None


class MessageUpdate(BaseModel):
    """Model for updating a message"""
    like: Optional[bool] = None
    read: Optional[bool] = None
    trashed_at: Optional[str] = None
    tags: Optional[str] = None


class ChannelCreate(BaseModel):
    """Model for creating a channel"""
    channel_id: Optional[str] = None
    channel_name: Optional[str] = None
    last_backup_timestamp: Optional[str] = None
    total_messages: Optional[int] = 0


class ChannelUpdate(BaseModel):
    """Model for updating a channel"""
    fetchstatus: Optional[str] = None
    fetchedStartedAt: Optional[str] = None
    fetchedEndedAt: Optional[str] = None
    last_backup_timestamp: Optional[str] = None


class TagBase(BaseModel):
    """Base model for tag data"""
    id: int
    name: str
    message_ids: Optional[str] = None


class TagCreate(BaseModel):
    """Model for creating a tag"""
    name: str
    message_ids: Optional[str] = None


class ChannelBase(BaseModel):
    id: int  # Primary key
    channel_id: Optional[str] = None  # Telegram channel ID
    channel_name: str
    total_messages: int
    last_backup_timestamp: Optional[str] = None
    fetchstatus: Optional[str] = None
    fetchedStartedAt: Optional[str] = None
    fetchedEndedAt: Optional[str] = None

    class Config:
        from_attributes = True


class ApiResponse(BaseModel):
    """Generic API response model"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Any] = None
    count: Optional[int] = None


class MessagesResponse(ApiResponse):
    """API response for messages"""
    data: Optional[List[MessageBase]] = None


class ChannelResponse(BaseModel):
    """Model for API response (without internal IDs if needed)"""
    channel_name: str
    total_messages: int
    last_backup_timestamp: Optional[str] = None
    fetchstatus: Optional[str] = None
    fetchedStartedAt: Optional[str] = None
    fetchedEndedAt: Optional[str] = None

class ChannelsResponse(BaseModel):
    success: bool
    data: List[ChannelBase]
    count: int


class StatsResponse(ApiResponse):
    """API response for statistics"""
    data: Optional[Dict[str, Any]] = None


class MessageTagsUpdate(BaseModel):
    """Model for updating message tags"""
    tags: str


class ChannelFetchStatusUpdate(BaseModel):
    """Model for updating channel fetch status"""
    fetchstatus: Optional[str] = None
    fetchedStartedAt: Optional[str] = None
    fetchedEndedAt: Optional[str] = None


class ScraperStartRequest(BaseModel):
    """Model for scraper start request"""
    days_back: Optional[int] = 3
    limit: Optional[int] = 1000
