import logging
from shutdown_handler import shutdown_manager

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Near the beginning of your main function or initialization code
shutdown_manager.setup()

# The rest of your application code remains unchanged 