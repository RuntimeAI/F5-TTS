import os
import logging
import telebot
import torch
import torchaudio
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
import numpy as np
import sys
import subprocess

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

def generate_audio_using_shell(text):
    """Generate audio using the shell script"""
    try:
        # Run the shell script and capture its output
        result = subprocess.run(['./tts_gen.sh', text], 
                              capture_output=True, 
                              text=True,
                              check=True)
        
        # Get the last line which contains the output file path
        output_file = result.stdout.strip().split('\n')[-1]
        
        return output_file
    except subprocess.CalledProcessError as e:
        logging.error(f"Shell script error: {e.stderr}")
        raise
    except Exception as e:
        logging.error(f"Error running shell script: {e}")
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
    """Generate cute voice using shell script"""
    try:
        # Get the text after the command
        text = message.text.replace('/gen_cute', '', 1).strip()
        if not text:
            bot.reply_to(message, "Please provide text after the command. Example: /gen_cute Hello world!")
            return

        # Send processing message
        processing_msg = bot.reply_to(message, "🎵 Generating voice... Please wait")

        # Generate audio using shell script
        output_file = generate_audio_using_shell(text)
        
        # Send audio
        with open(output_file, "rb") as audio_file:
            bot.send_voice(message.chat.id, audio_file)
        
        # Delete processing message
        bot.delete_message(message.chat.id, processing_msg.message_id)

    except Exception as e:
        logging.error(f"Error generating voice: {str(e)}")
        bot.reply_to(message, "Sorry, there was an error generating the voice. Please try again later.")

def delete_webhook():
    """Delete any existing webhook"""
    try:
        bot.delete_webhook()
        logging.info("Webhook deleted successfully")
    except Exception as e:
        logging.error(f"Error deleting webhook: {e}")
        raise

def main():
    """Start the bot."""
    logging.info("Bot started...")
    try:
        # Delete webhook before starting the bot
        delete_webhook()
        
        # Start polling
        bot.infinity_polling()
    except Exception as e:
        logging.error(f"Bot stopped due to error: {str(e)}")

if __name__ == '__main__':
    main()