import os
import logging
import telebot
import torch
import torchaudio
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
import numpy as np
import sys

# Add src directory to Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Modify import to handle potential LZMA issues
try:
    import lzma
except ImportError:
    logging.warning("LZMA module not available. Some compression features may be limited.")
    lzma = None

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize bot
bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))

def safe_import(module_path):
    """
    Safely import a module, logging any import errors.
    
    Args:
        module_path (str): Dot-separated module path to import
    
    Returns:
        module or None if import fails
    """
    try:
        module = __import__(module_path, fromlist=[''])
        return module
    except ImportError as e:
        logging.error(f"Could not import {module_path}: {e}")
        return None

def init_f5tts_minimal():
    """Initialize minimal F5-TTS components with enhanced error handling"""
    try:
        # Import F5TTS API
        from f5_tts.api import F5TTS
        
        # Initialize F5TTS with default model
        tts = F5TTS(
            model="F5-TTS",
            device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
            dtype=torch.float32
        )
        
        return tts
    
    except Exception as e:
        logging.error(f"Detailed initialization error: {e}")
        raise

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Send welcome message when /start command is received"""
    bot.reply_to(message, 
        "Hi! I'm a voice generation bot using F5-TTS.\n"
        "Use /gen_cute followed by your text to generate a cute voice.\n"
        "Example: /gen_cute Hello world!"
    )

@bot.message_handler(commands=['gen_cute'])
def generate_cute_voice(message):
    """Generate cute voice using F5-TTS"""
    try:
        # Get the text after the command
        text = message.text.replace('/gen_cute', '', 1).strip()
        if not text:
            bot.reply_to(message, "Please provide text after the command. Example: /gen_cute Hello world!")
            return

        # Send processing message
        processing_msg = bot.reply_to(message, "🎵 Generating voice... Please wait")

        # Generate audio using F5TTS
        wav, sr, _ = tts.infer(
            ref_file=os.getenv('REFERENCE_AUDIO'),
            ref_text="",  # Will auto-transcribe if empty
            gen_text=text,
            nfe_step=32,
            cfg_strength=2.0,
            remove_silence=True
        )
        
        # Save temporary file
        temp_path = "temp_output.wav"
        tts.export_wav(wav, temp_path, remove_silence=True)
        
        # Send audio
        with open(temp_path, "rb") as audio_file:
            bot.send_voice(message.chat.id, audio_file)
        
        # Delete processing message and temp file
        bot.delete_message(message.chat.id, processing_msg.message_id)
        os.remove(temp_path)

    except Exception as e:
        logging.error(f"Error generating voice: {str(e)}")
        bot.reply_to(message, "Sorry, there was an error generating the voice. Please try again later.")

# Initialize F5-TTS components
try:
    tts = init_f5tts_minimal()
    logging.info("F5-TTS initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize F5-TTS: {str(e)}")
    raise

def main():
    """Start the bot."""
    logging.info("Bot started...")
    try:
        bot.infinity_polling()
    except Exception as e:
        logging.error(f"Bot stopped due to error: {str(e)}")

if __name__ == '__main__':
    main()