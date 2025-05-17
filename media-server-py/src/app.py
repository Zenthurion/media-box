import logging
import asyncio
import os
import signal
import time
from src.shutdown_handler import shutdown_manager

# Import the server components from main.py
from src.main import Server

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
    
    logging.info("Initializing server...")
    server = Server()
    
    try:
        # Start the server
        await server.start()
        
        # Keep the application running
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        logging.error(f"Error in server: {e}")
        raise
    finally:
        if server:
            try:
                await server.stop()
            except Exception as e:
                logging.error(f"Error stopping server: {e}")

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