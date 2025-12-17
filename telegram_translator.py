# telegram_translator.py - FIXED VERSION
import pandas as pd
from googletrans import Translator
from tqdm import tqdm
import time

def translate_csv_with_cache(master_file='data/telegram_messages_master.csv', 
                           translated_file='data/telegram_translated_master.csv'):
    """
    Translate master CSV with caching - only translates new entries
    """
    print("="*60)
    print("🌐 TRANSLATION ENGINE")
    print("🌍 Russian → English | Incremental updates")
    print("="*60)
    
    # Initialize translator
    translator = Translator()
    
    # Read master file
    print(f"📖 Reading {master_file}...")
    try:
        df_master = pd.read_csv(master_file)
    except FileNotFoundError:
        print(f"❌ Master file not found: {master_file}")
        return
    
    # Check required columns
    if 'Message_Text' not in df_master.columns:
        print("❌ CSV must have 'Message_Text' column")
        return
    
    # Check if translated file exists
    try:
        df_translated = pd.read_csv(translated_file)
        print(f"📁 Found existing translations: {len(df_translated)} entries")
        
        # Get already translated message hashes
        if 'Message_Hash' in df_translated.columns:
            translated_hashes = set(df_translated['Message_Hash'].dropna())
        else:
            translated_hashes = set()
            print("⚠️  No Message_Hash in translated file - will translate all")
        
        # Find untranslated messages
        if 'Message_Hash' in df_master.columns:
            untranslated_mask = ~df_master['Message_Hash'].isin(translated_hashes)
            df_to_translate = df_master[untranslated_mask].copy()
            print(f"🆕 Found {len(df_to_translate)} new messages to translate")
        else:
            df_to_translate = df_master.copy()
            print(f"🔄 No Message_Hash in master - will translate all {len(df_to_translate)} messages")
        
    except FileNotFoundError:
        # No existing translations - translate everything
        print("📄 No existing translations found - starting fresh")
        df_to_translate = df_master.copy()
        df_translated = pd.DataFrame()
    
    if len(df_to_translate) == 0:
        print("✅ All messages already translated!")
        return
    
    # Add translation column
    df_to_translate = df_to_translate.copy()
    df_to_translate['Message_Text_Translated'] = ''
    
    # Translate with progress bar
    print(f"\n📝 Translating {len(df_to_translate)} messages...")
    
    with tqdm(total=len(df_to_translate), desc="Translating") as pbar:
        for i, row in df_to_translate.iterrows():
            try:
                text = row['Message_Text']
                if pd.notna(text) and str(text).strip() != '':
                    # Check if text contains Cyrillic (Russian)
                    cyrillic_count = sum(1 for char in str(text) if '\u0400' <= char <= '\u04FF')
                    if cyrillic_count > 0:
                        # Translate Russian text
                        translated = translator.translate(str(text), src='ru', dest='en').text
                        df_to_translate.at[i, 'Message_Text_Translated'] = translated
                    else:
                        # Keep English text as-is
                        df_to_translate.at[i, 'Message_Text_Translated'] = str(text)
                else:
                    df_to_translate.at[i, 'Message_Text_Translated'] = ''
                
                # Small delay to avoid rate limits
                time.sleep(0.1)
                
            except Exception as e:
                print(f"\n⚠️  Error translating row {i}: {e}")
                df_to_translate.at[i, 'Message_Text_Translated'] = str(row['Message_Text']) if pd.notna(row['Message_Text']) else ''
            
            pbar.update(1)
    
    # Combine with existing translations
    if not df_translated.empty:
        # Remove duplicates if any
        if 'Message_Hash' in df_translated.columns and 'Message_Hash' in df_to_translate.columns:
            existing_hashes = set(df_translated['Message_Hash'])
            df_to_translate = df_to_translate[~df_to_translate['Message_Hash'].isin(existing_hashes)]
        
        # Combine
        df_final = pd.concat([df_translated, df_to_translate], ignore_index=True)
    else:
        df_final = df_to_translate
    
    # Save to file
    df_final.to_csv(translated_file, index=False, encoding='utf-8')
    
    print(f"\n✅ TRANSLATION COMPLETE!")
    print(f"   Total translated entries: {len(df_final)}")
    print(f"   Newly translated: {len(df_to_translate)}")
    print(f"   Saved to: {translated_file}")