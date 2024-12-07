import os
import subprocess
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! Send me any text in Chinese or English, and I'll convert it to speech using the voice model."
    )

async def generate_tts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the input text from user
    text = update.message.text
    
    # Send a processing message
    processing_msg = await update.message.reply_text("Processing your text... Please wait.")
    
    try:
        # Call the tts_gen.sh script
        result = subprocess.run(
            ['./tts_gen.sh', text],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Get the output file path from the script's output
        output_file = result.stdout.strip().split('\n')[-1]
        
        # Send the audio file
        with open(output_file, 'rb') as audio:
            await update.message.reply_voice(audio)
        
        # Delete the processing message
        await processing_msg.delete()
        
    except subprocess.CalledProcessError as e:
        await processing_msg.edit_text(f"Error generating audio: {e.stderr}")
    except Exception as e:
        await processing_msg.edit_text(f"An error occurred: {str(e)}")

def main():
    # Create application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_tts))

    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
