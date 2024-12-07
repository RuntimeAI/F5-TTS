#!/bin/bash

# Check if text input is provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide the text to generate"
    echo "Usage: ./tts_gen.sh \"Your text here\""
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p ./output_audio

# Generate timestamp
timestamp=$(date +"%Y%m%d_%H%M%S")
output_file="./output_audio/tts_${timestamp}.wav"

# Use pre-transcribed reference audio
REF_AUDIO="sucai_dm.wav"
REF_TEXT="你愿意全部交给姐姐吗不愿意啊那你可别忘了我手机里的照片"

# Run F5 TTS command with the provided input
f5-tts_infer-cli \
    --model "F5-TTS" \
    --ref_audio "$REF_AUDIO" \
    --ref_text "$REF_TEXT" \
    --gen_text "$1" \
    --output "$output_file"

# Check if generation was successful
if [ $? -eq 0 ]; then
    echo "Generated audio saved to: $output_file"
    echo "$output_file"  # Return the file path
else
    echo "Error: Failed to generate audio"
    exit 1
fi
