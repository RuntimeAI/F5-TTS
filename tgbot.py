import os
import logging
import telebot
from f5_tts.api import F5TTS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize bot and F5-TTS
bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))
f5tts = F5TTS()

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

        # Generate audio using F5-TTS
        wav, sr, _ = f5tts.infer(
            ref_file=os.getenv('REFERENCE_AUDIO'),
            ref_text="",  # Empty for auto-transcription
            gen_text=text,
            file_wave="temp_output.wav"
        )

        # Send the generated audio
        with open("temp_output.wav", "rb") as audio:
            bot.send_voice(message.chat.id, audio)
        
        # Delete processing message
        bot.delete_message(message.chat.id, processing_msg.message_id)
        
        # Clean up temporary file
        os.remove("temp_output.wav")

    except Exception as e:
        logging.error(f"Error generating voice: {str(e)}")
        bot.reply_to(message, "Sorry, there was an error generating the voice. Please try again later.")

def main():
    """Start the bot."""
    logging.info("Bot started...")
    try:
        bot.infinity_polling()
    except Exception as e:
        logging.error(f"Bot stopped due to error: {str(e)}")

if __name__ == '__main__':
    main()