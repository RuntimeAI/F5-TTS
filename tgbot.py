import os
import subprocess
import telebot
import logging
from datetime import datetime
from dotenv import load_dotenv

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
    # Log user info and request
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID:{message.from_user.id}"
    text = message.text.replace('/tts_gen', '', 1).strip()
    request_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info(f"TTS Request - User: {user_info}, Text: {text}, Time: {request_time}")
    
    # Check if text was provided
    if not text:
        logger.warning(f"Empty text provided by user {user_info}")
        bot.reply_to(message, "Please provide text after the command.\nExample: /tts_gen Hello World!")
        return
    
    # Send processing message with status
    status_text = (
        "🎯 Processing your request:\n"
        "⌛ Initializing TTS generation...\n"
        "📝 Text length: {} characters"
    ).format(len(text))
    
    processing_msg = bot.reply_to(message, status_text)
    
    try:
        # Update status - Starting TTS
        bot.edit_message_text(
            status_text + "\n🔄 Generating audio...",
            message.chat.id,
            processing_msg.message_id
        )
        
        # Call the tts_gen.sh script
        logger.info(f"Starting TTS generation for user {user_info}")
        result = subprocess.run(
            ['./tts_gen.sh', text],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Get the output file path
        output_file = result.stdout.strip().split('\n')[-1]
        file_size = os.path.getsize(output_file) / 1024  # Size in KB
        
        # Update status - Sending file
        bot.edit_message_text(
            status_text + f"\n✅ Audio generated successfully!\n📤 Sending file ({file_size:.1f}KB)...",
            message.chat.id,
            processing_msg.message_id
        )
        
        # Send the audio file
        with open(output_file, 'rb') as audio:
            bot.send_voice(message.chat.id, audio)
        
        # Log success
        logger.info(f"Successfully generated and sent audio for user {user_info}")
        
        # Delete processing message
        bot.delete_message(message.chat.id, processing_msg.message_id)
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Error generating audio: {e.stderr}"
        logger.error(f"TTS generation failed for user {user_info}: {error_msg}")
        bot.edit_message_text(
            f"❌ {error_msg}", 
            message.chat.id, 
            processing_msg.message_id
        )
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        logger.error(f"Unexpected error for user {user_info}: {error_msg}")
        bot.edit_message_text(
            f"❌ {error_msg}", 
            message.chat.id, 
            processing_msg.message_id
        )

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
