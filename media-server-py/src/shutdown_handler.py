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
import asyncio
import subprocess

# Add the src directory to path so we can import from our modules
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from services.display.eink_manager import EinkDisplayManager

class ShutdownManager:
    def __init__(self):
        self.display_manager = None

    def _display_shutdown_screen(self):
        """Show shutdown logo and cleanup display hardware."""
        if not self.display_manager:
            return
        try:
            logging.info("Displaying logo before shutdown")
            self.display_manager.show_logo()

            # Allow the display time to refresh
            logging.info("Waiting for display to update...")
            time.sleep(3)

            logging.info("Cleaning up display")
            self.display_manager.cleanup()
            logging.info("Display cleanup complete")
        except Exception as e:
            logging.error(f"Error during shutdown display: {e}")
            import traceback
            logging.error(traceback.format_exc())
        
    def setup(self):
        """Set up the shutdown handler"""
        logging.info("Setting up shutdown handler")
        
        # Initialize display manager with refresh_task=False to avoid asyncio error
        self.display_manager = EinkDisplayManager(start_refresh_task=False)
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        
        logging.info("Shutdown handler configured")
        logging.info("==== SHUTDOWN HANDLER SETUP COMPLETE ====")
        
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signal by displaying logo and then exiting"""
        logging.info(f"Received signal {signum}, preparing for shutdown")
        
        # Show logo before shutdown
        self._display_shutdown_screen()

        logging.info("Exiting application")
        sys.exit(0)

    def _run_shutdown_sequence(self):
        """Perform shutdown display then request system halt."""
        self._display_shutdown_screen()

        try:
            subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
        except FileNotFoundError:
            logging.error("Could not find shutdown command; exiting process instead")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to initiate system shutdown: {e}")

        # Ensure the process exits even if shutdown command fails
        sys.exit(0)

    async def shutdown(self):
        """Initiate shutdown from async context (e.g., MQTT command)."""
        logging.info("Shutdown command received; initiating system shutdown")
        await asyncio.to_thread(self._run_shutdown_sequence)

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
