# main.py
import asyncio
import os
from telegram_auth import TelegramAuth
from telegram_fetch import MessageFetcher
from telegram_csv import CSVHandler

async def main():
    """Main orchestrator - ties everything together"""
    print("="*60)
    print("🤖 TELEGRAM MESSAGE SCRAPER")
    print("🌍 Timezone: Asia/Kolkata | Days: Last 3")
    print("="*60)
    
    # Create output directory
    output_dir = './telegram_data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize components
    csv_handler = CSVHandler(output_dir)
    
    # Authenticate and get channels
    async with TelegramAuth() as auth:
        if not auth.client:
            return
        
        # Get all channels
        channels_data = await auth.get_all_channels(limit=50)
        
        if not channels_data:
            print("❌ No channels found!")
            return
        
        # Show channel list
        print(f"\n📋 FOUND {len(channels_data)} CHANNELS:")
        for i, channel in enumerate(channels_data, 1):
            print(f"  {i:2}. {channel['name']:30} ({channel['type']})")
        
        
        # Initialize message fetcher
        fetcher = MessageFetcher(auth.client)
        
        # Process each channel
        print("\n" + "="*60)
        print("🚀 PROCESSING CHANNELS")
        print("="*60)
        
        all_channel_messages = []
        csv_files = []
        successful_channels = 0
        total_messages = 0
        
        for i, channel_data in enumerate(channels_data, 1):
            print(f"\n[{i}/{len(channels_data)}] ", end="")
            
            # Fetch messages
            messages = await fetcher.fetch_messages(
                channel_data['dialog'],
                days_back=3,
                limit=1000
            )
            
            if messages:
                # Save to individual CSV
                csv_file = csv_handler.save_channel_messages(
                    messages, 
                    channel_data['name']
                )
                
                if csv_file:
                    csv_files.append(csv_file)
                    all_channel_messages.append(messages)
                    successful_channels += 1
                    total_messages += len(messages)
        
        # Create summary
        print("\n" + "="*60)
        print("📊 PROCESSING SUMMARY")
        print("="*60)
        print(f"Total channels processed: {len(channels_data)}")
        print(f"Channels with messages: {successful_channels}")
        print(f"Total messages fetched: {total_messages}")
        print(f"CSV files created: {len(csv_files)}")
        
        if csv_files:
            print("\n📁 CSV FILES SAVED:")
            for csv_file in csv_files:
                print(f"  • {os.path.basename(csv_file)}")
                
            csv_handler.save_all_messages(all_channel_messages)
        
        print("\n✨ Processing complete!")
        print(f"📁 Output directory: {os.path.abspath(output_dir)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")