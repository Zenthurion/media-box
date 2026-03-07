## E-Paper Display Setup

This project uses a Waveshare 2.13" e-ink display. To set up the display:

### Automatic Installation

Run the installation script:

## E-Paper Display Support

This project includes built-in support for a Waveshare 2.13" e-ink display.

### Docker Environment

When running in Docker, the display functionality automatically runs in simulation mode.
No additional configuration is needed.

### Hardware Setup (Raspberry Pi)

If running directly on a Raspberry Pi with the e-ink display connected:

1. Ensure SPI is enabled:

## Build and publish Docker image (Option 1)

Use this when you want to build from source on your dev machine and push the latest image for the Pi to pull.

### Build + push (dev machine)

NB! Requires Docker Desktop to be running

```bash
cd media-server-py
docker buildx create --use
docker buildx build --platform linux/arm/v7 -t zenthurion/media-server-py-app:latest --push .
```

### Pull on Raspberry Pi

```bash
docker pull zenthurion/media-server-py-app:latest
```

Restart the container/service using your normal method (docker-compose or systemd).
