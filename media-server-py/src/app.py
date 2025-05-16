import logging
from shutdown_handler import shutdown_manager
import os
import signal
import time

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Near the beginning of your main function or initialization code
shutdown_manager.setup()

# The rest of your application code remains unchanged 

def test_shutdown():
    """Test the shutdown process"""
    print("Testing shutdown sequence in 3 seconds...")
    time.sleep(3)
    print("Triggering shutdown handler...")
    os.kill(os.getpid(), signal.SIGTERM)

# If you want to test it, uncomment this line
# test_shutdown() 