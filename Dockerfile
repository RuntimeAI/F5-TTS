FROM pytorch/pytorch:2.4.0-cuda12.4-cudnn9-devel

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install fastapi uvicorn pydantic

# Install F5-TTS
RUN pip install git+https://github.com/SWivid/F5-TTS.git

# Copy web service code
COPY web_service.py .

# Expose port
EXPOSE 8000

# Run the service
CMD ["python", "web_service.py"]