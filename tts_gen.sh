#!/bin/bash

# Check if text input is provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide the text to generate"
    echo "Usage: ./tts_gen.sh \"Your text here\""
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p ./output_audio

# Use ramdisk for temporary files
TEMP_DIR="/dev/shm/tts_temp"
mkdir -p "$TEMP_DIR"

# Clean old files (older than 1 hour)
find "$TEMP_DIR" -type f -mmin +60 -delete

# Generate timestamp
timestamp=$(date +"%Y%m%d_%H%M%S")
output_file="$TEMP_DIR/tts_${timestamp}.wav"

# Use pre-transcribed reference audio
REF_AUDIO="sucai_dm.wav"
REF_TEXT="你愿意全部交给姐姐吗不愿意啊那你可别忘了我手机里的照片"

# Run F5 TTS command with optimized settings
CUDA_VISIBLE_DEVICES=0 f5-tts_infer-cli \
    --model "F5-TTS" \
    --ref_audio "$REF_AUDIO" \
    --ref_text "$REF_TEXT" \
    --gen_text "$1" \
    --output_file "$output_file"

# Move to permanent storage if successful
if [ $? -eq 0 ]; then
    mv "$output_file" "./output_audio/"
    final_output="./output_audio/tts_${timestamp}.wav"
    echo "Generated audio saved to: $final_output"
    echo "$final_output"
else
    echo "Error: Failed to generate audio"
    exit 1
fi
