import os
import subprocess
import telebot
import logging
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# Initialize thread pool
executor = ThreadPoolExecutor(max_workers=3)  # Limit concurrent generations

# Cache for recently generated audio
audio_cache = {}
MAX_CACHE_SIZE = 100  # Maximum number of cached items

def generate_audio(text):
    """Separate function for audio generation to be run in thread"""
    result = subprocess.run(
        ['./tts_gen.sh', text],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip().split('\n')[-1]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID:{message.from_user.id}"
    logger.info(f"New user {user_info} started the bot")
    
    bot.reply_to(message, 
        "Hello! Use the /tts_gen command followed by your text to convert it to speech.\n"
        "Example: /tts_gen Hello World! or /tts_gen 你好世界！"
    )

@bot.message_handler(commands=['tts_gen'])
def generate_tts(message):
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID:{message.from_user.id}"
    text = message.text.replace('/tts_gen', '', 1).strip()
    
    # Check if text was provided
    if not text:
        logger.warning(f"Empty text provided by user {user_info}")
        bot.reply_to(message, "Please provide text after the command.\nExample: /tts_gen Hello World!")
        return
    
    # Check cache first
    cache_key = text[:100]  # Use first 100 chars as key
    if cache_key in audio_cache:
        logger.info(f"Cache hit for text: {text[:30]}...")
        with open(audio_cache[cache_key], 'rb') as audio:
            bot.send_voice(message.chat.id, audio)
        return

    processing_msg = bot.reply_to(message, "⌛ Queued for processing...")
    
    def process_audio():
        try:
            # Update status
            bot.edit_message_text(
                "🎯 Processing:\n⌛ Generating audio...",
                message.chat.id,
                processing_msg.message_id
            )
            
            # Generate audio in thread
            output_file = generate_audio(text)
            
            # Cache the result
            if len(audio_cache) >= MAX_CACHE_SIZE:
                # Remove oldest item
                oldest_key = next(iter(audio_cache))
                audio_cache.pop(oldest_key)
            audio_cache[cache_key] = output_file
            
            # Send the audio
            with open(output_file, 'rb') as audio:
                bot.send_voice(message.chat.id, audio)
            
            # Delete processing message
            bot.delete_message(message.chat.id, processing_msg.message_id)
            logger.info(f"Successfully processed request for {user_info}")
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(f"Error for {user_info}: {error_msg}")
            bot.edit_message_text(
                f"❌ {error_msg}",
                message.chat.id,
                processing_msg.message_id
            )
    
    # Submit task to thread pool
    executor.submit(process_audio)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID:{message.from_user.id}"
    logger.info(f"Received invalid message from {user_info}: {message.text}")
    bot.reply_to(message, "Please use the /tts_gen command to generate speech.\nExample: /tts_gen Hello World!")

# Start the bot
if __name__ == '__main__':
    logger.info("Bot started successfully")
    print("Bot is running...")
    bot.infinity_polling()
