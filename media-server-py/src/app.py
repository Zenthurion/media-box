import logging
import asyncio
import os
import signal
import time
from shutdown_handler import shutdown_manager

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main application entry point"""
    logging.info("Starting application...")
    
    # Set up shutdown handler
    shutdown_manager.setup()
    
    # Keep the application running
    while True:
        await asyncio.sleep(1)

def test_shutdown():
    """Test the shutdown process"""
    print("Testing shutdown sequence in 3 seconds...")
    time.sleep(3)
    print("Triggering shutdown handler...")
    os.kill(os.getpid(), signal.SIGTERM)

# If this file is run directly, start the app
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logging.error(f"Error in main: {e}")
        import traceback
        logging.error(traceback.format_exc()) 