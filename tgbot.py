import os
import logging
import telebot
import torch
import torchaudio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize bot
bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))

# Initialize F5-TTS components directly
def init_f5tts():
    from f5_tts.model.cfm import CFM
    from f5_tts.model.dit import DiT
    from f5_tts.utils.audio import load_audio
    from f5_tts.utils.tokenizer import get_tokenizer
    from f5_tts.utils.vocoder import load_vocoder
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Load vocoder
    vocoder = load_vocoder("vocos", is_local=False)
    
    # Load tokenizer
    vocab_char_map, vocab_size = get_tokenizer("pinyin")
    
    # Model configuration
    model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)
    
    # Initialize model
    model = CFM(
        transformer=DiT(**model_cfg, text_num_embeds=vocab_size, mel_dim=100),
        mel_spec_kwargs=dict(
            n_fft=1024,
            hop_length=256,
            win_length=1024,
            n_mel_channels=100,
            target_sample_rate=24000,
            mel_spec_type="vocos"
        ),
        vocab_char_map=vocab_char_map
    ).to(device)
    
    # Load checkpoint
    from huggingface_hub import hf_hub_download
    ckpt_path = hf_hub_download("SWivid/F5-TTS/F5TTS_Base", "model_1200000.safetensors")
    model.load_state_dict(torch.load(ckpt_path, map_location=device))
    model.eval()
    
    return model, vocoder, device

# Initialize F5-TTS components
try:
    model, vocoder, device = init_f5tts()
    logging.info("F5-TTS initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize F5-TTS: {str(e)}")
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

        # Load reference audio
        ref_audio, sr = torchaudio.load(os.getenv('REFERENCE_AUDIO'))
        if ref_audio.shape[0] > 1:
            ref_audio = torch.mean(ref_audio, dim=0, keepdim=True)
        ref_audio = ref_audio.to(device)

        # Generate audio
        with torch.inference_mode():
            generated = model.sample(
                cond=ref_audio,
                text=[text],
                duration=int(len(text) * 256),  # Approximate duration
                steps=32,
                cfg_strength=2.0
            )
            audio = vocoder.decode(generated.permute(0, 2, 1))
            audio = audio.cpu().squeeze().numpy()

        # Save and send audio
        torchaudio.save("temp_output.wav", torch.tensor(audio).unsqueeze(0), 24000)
        
        with open("temp_output.wav", "rb") as audio_file:
            bot.send_voice(message.chat.id, audio_file)
        
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