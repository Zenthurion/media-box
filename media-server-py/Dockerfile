# Use ARM-compatible Python image
FROM --platform=linux/arm/v7 python:3.11-slim-bullseye

# Install VLC, ffmpeg and other dependencies
RUN apt-get update && apt-get install -y \
    vlc \
    ffmpeg \
    pulseaudio \
    alsa-utils \
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

# Copy the rest of the application
COPY src/ ./src/

# Run the application
CMD ["python", "-m", "src.main"]