# Use ARM-compatible Python image
FROM --platform=linux/arm/v7 python:3.11-slim-bullseye

# Install system dependencies including build tools and development packages
RUN apt-get update && apt-get install -y \
    vlc \
    ffmpeg \
    pulseaudio \
    alsa-utils \
    gcc \
    python3-dev \
    zlib1g-dev \
    libjpeg-dev \
    build-essential \
    # Add these new dependencies for PIL font support
    libfreetype6-dev \
    libfreetype6 \
    git \
    python3-pip \
    python3-pil \
    python3-numpy \
    # Remove spidev and RPi.GPIO from here
    && rm -rf /var/lib/apt/lists/*

# Configure PulseAudio - ensure pulse user is in audio group without failing if user exists
RUN getent passwd pulse || useradd -m -d /var/lib/pulse pulse \
    && getent group audio || groupadd audio \
    && usermod -aG audio pulse \
    && mkdir -p /var/run/pulse /var/lib/pulse \
    && chown -R pulse:pulse /var/run/pulse /var/lib/pulse

# Set up VLC to use a more container-friendly audio output
ENV VLC_PLUGIN_PATH=/usr/lib/vlc/plugins
ENV PULSE_SERVER=unix:/tmp/pulse-socket
ENV PULSE_COOKIE=/tmp/pulse-cookie

# Configure VLC to use dummy audio output if PulseAudio fails
ENV VLC_AUDIO=dummy

# Create and set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create the entrypoint script directly in the container
RUN echo '#!/bin/bash' > /app/entrypoint.sh && \
    echo 'set -e' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# Forward all signals to the Python process' >> /app/entrypoint.sh && \
    echo 'trap "kill -TERM \$PID" TERM INT' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# Start the Python application in the background' >> /app/entrypoint.sh && \
    echo 'python3 -u /app/src/app.py &' >> /app/entrypoint.sh && \
    echo 'PID=\$!' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# Wait for the Python process to exit' >> /app/entrypoint.sh && \
    echo 'wait \$PID' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# Exit with the same code' >> /app/entrypoint.sh && \
    echo 'exit \$?' >> /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Copy the rest of the application
COPY src/ ./src/

# Install Python dependencies (moved from apt-get)
RUN pip3 install spidev RPi.GPIO

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV WAVESHARE_HAT=1

# Add this line to your Dockerfile to copy the logo file
COPY logo.png /app/logo.png

# Change CMD to use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
CMD []