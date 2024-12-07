import os
import subprocess
import telebot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Initialize bot
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 
        "Hello! Use the /tts_gen command followed by your text to convert it to speech.\n"
        "Example: /tts_gen Hello World! or /tts_gen 你好世界！"
    )

@bot.message_handler(commands=['tts_gen'])
def generate_tts(message):
    # Get text after command
    text = message.text.replace('/tts_gen', '', 1).strip()
    
    # Check if text was provided
    if not text:
        bot.reply_to(message, "Please provide text after the command.\nExample: /tts_gen Hello World!")
        return
    
    # Send processing message
    processing_msg = bot.reply_to(message, "Processing your text... Please wait.")
    
    try:
        # Call the tts_gen.sh script
        result = subprocess.run(
            ['./tts_gen.sh', text],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Get the output file path
        output_file = result.stdout.strip().split('\n')[-1]
        
        # Send the audio file
        with open(output_file, 'rb') as audio:
            bot.send_voice(message.chat.id, audio)
        
        # Delete processing message
        bot.delete_message(message.chat.id, processing_msg.message_id)
        
    except subprocess.CalledProcessError as e:
        bot.edit_message_text(
            f"Error generating audio: {e.stderr}", 
            message.chat.id, 
            processing_msg.message_id
        )
    except Exception as e:
        bot.edit_message_text(
            f"An error occurred: {str(e)}", 
            message.chat.id, 
            processing_msg.message_id
        )

# Start the bot
if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
