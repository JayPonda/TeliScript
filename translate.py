import pandas as pd
from googletrans import Translator
from tqdm import tqdm
import time

# Initialize translator
translator = Translator()

def translate_text(text, src='ru', dest='en'):
    """Translate text with error handling"""
    if pd.isna(text) or str(text).strip() == '':
        return text
    
    try:
        # Translate the text
        translated = translator.translate(str(text), src=src, dest=dest)
        return translated.text
    except Exception as e:
        print(f"Error translating: {text[:50]}... - {e}")
        return text  # Return original text on error

def translate_csv(input_file, output_file, batch_size=50, delay=0.1):
    """
    Translate Message_Text column in CSV file
    
    Parameters:
    - input_file: Path to input CSV
    - output_file: Path to output CSV
    - batch_size: Number of texts to process in memory
    - delay: Delay between batches to avoid rate limits
    """
    
    # Read CSV
    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file)
    
    # Check if Message_Text column exists
    if 'Message_Text' not in df.columns:
        raise ValueError("CSV file must have 'Message_Text' column")
    
    print(f"Found {len(df)} rows with {df['Message_Text'].notna().sum()} non-empty messages")
    
    # Create new column for translations
    df['Message_Text_Translated'] = ""
    
    # Translate with progress bar
    print("Translating messages...")
    for i in tqdm(range(0, len(df), batch_size)):
        batch = df.iloc[i:i+batch_size]
        
        # Get texts to translate
        texts = batch['Message_Text'].fillna('').tolist()
        
        try:
            # Translate batch
            translations = []
            for text in texts:
                translated = translate_text(text)
                translations.append(translated)
            
            # Update DataFrame
            df.loc[i:i+batch_size-1, 'Message_Text_Translated'] = translations
            
            # Small delay to avoid rate limiting
            time.sleep(delay)
            
        except Exception as e:
            print(f"Error in batch {i//batch_size}: {e}")
            # Fallback: translate one by one
            for j in range(i, min(i+batch_size, len(df))):
                df.at[j, 'Message_Text_Translated'] = translate_text(df.at[j, 'Message_Text'])
    
    # Save to new CSV
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Translation complete! Saved to {output_file}")
    print(f"Original column: 'Message_Text'")
    print(f"New column added: 'Message_Text_Translated'")

# Usage
if __name__ == "__main__":
    input_csv = "data/telegram_messages_master.csv"  # Change this
    output_csv = "data/translated_output.csv"  # Change this
    
    translate_csv(input_csv, output_csv)