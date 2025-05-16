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
            logging.info("Displaying logo before shutdown")
            self.display_manager.show_logo()
            
            # Give time for display to update
            time.sleep(2)
            
            # Cleanup display
            self.display_manager.cleanup()
        
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
    main() 