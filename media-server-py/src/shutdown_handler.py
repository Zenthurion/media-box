#!/usr/bin/env python3
"""
Handles graceful shutdown of the application, displaying logo on e-ink before exit
"""
import os
import sys
import signal
import logging
import time
from pathlib import Path

# Add the src directory to path so we can import from our modules
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from services.display.eink_manager import EinkDisplayManager

class ShutdownManager:
    def __init__(self):
        self.display_manager = None
        
    def setup(self):
        """Set up the shutdown handler"""
        logging.info("Setting up shutdown handler")
        
        # Initialize display manager
        self.display_manager = EinkDisplayManager()
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        
        logging.info("Shutdown handler configured")
        
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signal by displaying logo and then exiting"""
        logging.info(f"Received signal {signum}, preparing for shutdown")
        
        # Show logo before shutdown
        if self.display_manager:
            try:
                logging.info("Displaying logo before shutdown")
                self.display_manager.show_logo()
                
                # Increase time for display to update - Docker gives 10 seconds by default
                logging.info("Waiting for display to update...")
                time.sleep(3)
                
                # Cleanup display
                logging.info("Cleaning up display")
                self.display_manager.cleanup()
                logging.info("Display cleanup complete")
            except Exception as e:
                logging.error(f"Error during shutdown display: {e}")
                import traceback
                logging.error(traceback.format_exc())
        
        logging.info("Exiting application")
        sys.exit(0)

# Instantiate for import in other modules
shutdown_manager = ShutdownManager()

def main():
    """Run as standalone to test shutdown sequence"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    shutdown_manager.setup()
    
    # Simulate running application
    logging.info("Application running. Press Ctrl+C to test shutdown sequence")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check if we're testing shutdown sequence
    if len(sys.argv) > 1 and sys.argv[1] == "--test-shutdown":
        print("Setting up shutdown manager...")
        shutdown_manager.setup()
        print("Triggering shutdown sequence...")
        shutdown_manager.handle_shutdown(signal.SIGTERM, None)
    else:
        main() 