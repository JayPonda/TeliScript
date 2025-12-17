import asyncio
from datetime import datetime, timedelta
from telethon import TelegramClient
import pytz
import os
import sys

def validate_environment():
    """Validate and load environment variables"""
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("💡 Create a .env file with these contents:")
        print("""
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE_NUMBER=+1234567890
""")
        sys.exit(1)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE_NUMBER')
    
    errors = []
    if not api_id:
        errors.append("TELEGRAM_API_ID not set")
    elif not api_id.isdigit():
        errors.append("TELEGRAM_API_ID must contain only digits")
    
    if not api_hash:
        errors.append("TELEGRAM_API_HASH not set")
    
    if not phone:
        errors.append("TELEGRAM_PHONE_NUMBER not set")
    elif not phone.startswith('+'):
        errors.append("TELEGRAM_PHONE_NUMBER must start with '+'")
    
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        sys.exit(1)
    
    return int(api_id), api_hash, phone

async def main():
    """Complete working script - all in one async context"""
    print("="*60)
    print("📱 TELEGRAM MESSAGE FETCHER - LAST 3 DAYS")
    print("🌍 Timezone: Asia/Kolkata")
    print("="*60)
    
    # Validate environment
    API_ID, API_HASH, PHONE = validate_environment()
    
    # Start client in a single async context
    async with TelegramClient('telegram_session', API_ID, API_HASH) as client:
        try:
            await client.start(PHONE)
            me = await client.get_me()
            print(f"✅ Logged in as: {me.first_name or 'User'}")
            
            # ===== STEP 1: LIST ALL CHANNELS =====
            print("\n📱 Your Channels:")
            print("="*60)
            
            channels = []
            async for dialog in client.iter_dialogs(limit=50):
                if dialog.is_channel or dialog.is_group:
                    channels.append(dialog)
                    print(f"{len(channels)}. {dialog.name}")
            
            if not channels:
                print("❌ No channels found!")
                return
            
            # ===== STEP 2: SELECT CHANNEL =====
            while True:
                try:
                    choice = input(f"\n🔢 Select channel (1-{len(channels)}): ").strip()
                    if not choice:
                        continue
                    
                    idx = int(choice) - 1
                    if 0 <= idx < len(channels):
                        selected = channels[idx]
                        print(f"\n✅ Selected: {selected.name} (ID: {selected.entity.id})")
                        break
                    else:
                        print(f"❌ Please enter 1-{len(channels)}")
                except ValueError:
                    print("❌ Please enter a number")
            
            # ===== STEP 3: GET LAST 3 DAYS MESSAGES =====
            print("\n📅 Getting messages from last 3 days...")
            print("="*60)
            
            tz = pytz.timezone('Asia/Kolkata')
            now_local = datetime.now(tz)
            start_date_local = now_local - timedelta(days=3)
            
            print(f"Date range: {start_date_local.strftime('%Y-%m-%d %H:%M')} to {now_local.strftime('%Y-%m-%d %H:%M')}")
            print(f"Timezone: Asia/Kolkata")
            print("-"*60)
            
            # Convert to UTC for comparison
            start_date_utc = start_date_local.astimezone(pytz.UTC)
            
            # Fetch messages
            messages = []
            message_count = 0
            
            async for message in client.iter_messages(selected.entity, limit=500):
                message_count += 1
                msg_utc = message.date.replace(tzinfo=pytz.UTC)
                
                # Stop if we're getting messages older than 3 days
                if msg_utc < start_date_utc:
                    print(f"⏹️  Stopping at message from {msg_utc.strftime('%Y-%m-%d')} (older than 3 days)")
                    break
                
                # Convert to local time
                msg_local = msg_utc.astimezone(tz)
                
                # Only include if within last 3 days
                if start_date_local <= msg_local <= now_local:
                    messages.append({
                        'datetime_utc': msg_utc,
                        'datetime_local': msg_local,
                        'message': message
                    })
            
            print(f"📊 Scanned {message_count} recent messages")
            
            # ===== STEP 4: DISPLAY RESULTS =====
            if not messages:
                print("\n📭 No messages found in the last 3 days.")
                print("\n💡 Try increasing the limit from 500 to 1000 or more.")
                return
            
            print(f"\n🎯 FOUND {len(messages)} MESSAGES FROM LAST 3 DAYS")
            print("="*60)
            
            # Group by date
            messages_by_date = {}
            for item in messages:
                date_key = item['datetime_local'].strftime('%Y-%m-%d')
                if date_key not in messages_by_date:
                    messages_by_date[date_key] = []
                messages_by_date[date_key].append(item)
            
            # Display by date (most recent first)
            for date in sorted(messages_by_date.keys(), reverse=True):
                print(f"\n📅 {date}:")
                print("-"*40)
                
                for item in sorted(messages_by_date[date], key=lambda x: x['datetime_local']):
                    msg = item['message']
                    time_str = item['datetime_local'].strftime('%H:%M:%S')
                    
                    # Get sender info
                    sender = await msg.get_sender()
                    sender_name = selected.name
                    if sender:
                        if hasattr(sender, 'title'):
                            sender_name = sender.title
                        elif hasattr(sender, 'first_name'):
                            sender_name = sender.first_name
                            if hasattr(sender, 'last_name') and sender.last_name:
                                sender_name += f" {sender.last_name}"
                    
                    # Get message content
                    if msg.text:
                        content = msg.text
                        # Show first line or first 150 chars
                        lines = content.split('\n')
                        preview = lines[0][:150] if lines[0] else "[Empty]"
                        if len(lines) > 1 or len(lines[0]) > 150:
                            preview += "..."
                    elif msg.media:
                        media_type = msg.media.__class__.__name__.replace('MessageMedia', '')
                        preview = f"[📎 {media_type}]"
                    else:
                        preview = "[No content]"
                    
                    print(f"🕒 {time_str} | 👤 {sender_name}")
                    print(f"   {preview}")
                    print()
            
            # ===== STEP 5: OPTION TO SAVE =====
            save_choice = input("\n💾 Save messages to CSV? (y/N): ").strip().lower()
            if save_choice == 'y':
                import csv
                
                # Clean filename
                clean_name = "".join(c if c.isalnum() or c in ' _-' else '_' for c in selected.name)
                filename = f"telegram_{clean_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Date', 'Time', 'Sender', 'Message'])
                    
                    for item in messages:
                        msg = item['message']
                        date_str = item['datetime_local'].strftime('%Y-%m-%d')
                        time_str = item['datetime_local'].strftime('%H:%M:%S')
                        
                        sender = await msg.get_sender()
                        sender_name = selected.name
                        if sender:
                            if hasattr(sender, 'title'):
                                sender_name = sender.title
                            elif hasattr(sender, 'first_name'):
                                sender_name = sender.first_name
                        
                        message_text = ""
                        if msg.text:
                            message_text = msg.text.replace('\n', ' ').replace('\r', ' ')[:500]
                        elif msg.media:
                            message_text = f"[Media: {msg.media.__class__.__name__}]"
                        else:
                            message_text = "[No content]"
                        
                        writer.writerow([date_str, time_str, sender_name, message_text])
                
                print(f"✅ Saved to: {os.path.abspath(filename)}")
            
            print("\n✨ Done!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")