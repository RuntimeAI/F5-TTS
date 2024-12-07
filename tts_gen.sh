#!/bin/bash

# Check if text input is provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide the text to generate"
    echo "Usage: ./tts_gen.sh \"Your text here\""
    exit 1
fi

# Run F5 TTS command with the provided input
f5-tts_infer-cli \
    --model "F5-TTS" \
    --ref_audio "sucai_dm.wav" \
    --ref_text "" \
    --gen_text "$1"
