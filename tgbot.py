import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from f5_tts.api import F5TTS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize F5-TTS
f5tts = F5TTS()

async def gen_cute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate cute voice using F5-TTS"""
    try:
        # Get the text after the command
        text = ' '.join(context.args)
        if not text:
            await update.message.reply_text("Please provide text after the command. Example: /gen-cute Hello world!")
            return

        # Send processing message
        processing_msg = await update.message.reply_text("🎵 Generating voice... Please wait")

        # Generate audio using F5-TTS
        wav, sr, _ = f5tts.infer(
            ref_file=os.getenv('REFERENCE_AUDIO'),
            ref_text="",  # Empty for auto-transcription
            gen_text=text,
            file_wave="temp_output.wav"
        )

        # Send the generated audio
        with open("temp_output.wav", "rb") as audio:
            await update.message.reply_voice(audio)
        
        # Delete processing message
        await processing_msg.delete()
        
        # Clean up temporary file
        os.remove("temp_output.wav")

    except Exception as e:
        logging.error(f"Error generating voice: {str(e)}")
        await update.message.reply_text("Sorry, there was an error generating the voice. Please try again later.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Hi! I'm a voice generation bot using F5-TTS.\n"
        "Use /gen-cute followed by your text to generate a cute voice.\n"
        "Example: /gen-cute Hello world!"
    )

def main():
    """Start the bot."""
    # Get bot token from environment variable
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        raise ValueError("No bot token found in environment variables!")

    # Create the Application
    application = Application.builder().token(bot_token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gen-cute", gen_cute))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()