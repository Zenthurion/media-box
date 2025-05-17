#!/usr/bin/env python3
"""
Docker entrypoint script that sets up proper asyncio handling
"""
import asyncio
import sys
import signal
import logging
import os

# Add the src directory to the Python path
sys.path.append('/app')
sys.path.append('/app/src')

async def run_app():
    """Import and run the main application"""
    # Import here after event loop is established
    from src.main import main
    
    # Run the main application
    await main()


def handle_signal(signum, frame):
    """Handle Docker shutdown signals"""
    print(f'Signal received: {signum}, shutting down...')
    sys.exit(0)


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    
    # Run the app with proper asyncio support
    try:
        logging.info("Starting application via entrypoint...")
        asyncio.run(run_app())
        logging.info("Application main loop exited normally")
    except KeyboardInterrupt:
        print('Keyboard interrupt received, shutting down...')
    except Exception as e:
        print(f'Error running app: {e}')
        import traceback
        traceback.print_exc()
    finally:
        print("Application terminated") 