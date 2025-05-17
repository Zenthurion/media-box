#!/bin/bash
set -e

# Start the Python application with the correct event loop setup
python3 -u -c "
import asyncio
import sys
import time
import signal
import logging
import os

async def run_app():
    # Import after the event loop is established
    from src.app import main
    
    # Run the main app
    await main()

# Set up signal handlers
def handle_signal(signum, frame):
    print(f'Signal received: {signum}, shutting down...')
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

# Run the app
try:
    asyncio.run(run_app())
except KeyboardInterrupt:
    print('Keyboard interrupt received, shutting down...')
except Exception as e:
    print(f'Error running app: {e}')
    import traceback
    traceback.print_exc()
" 