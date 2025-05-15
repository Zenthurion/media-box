import logging
from PIL import Image

class EPDSimulator:
    """Simulated EPD class that mimics the behavior of the Waveshare EPD classes"""
    
    def __init__(self, width=250, height=122):
        self.width = width
        self.height = height
        self.FULL_UPDATE = 0
        self.PART_UPDATE = 1
        logging.info(f"EPD Simulator initialized with size {width}x{height}")
    
    def init(self, update=0):
        logging.info(f"EPD init (simulated) with update mode {update}")
        return 0
    
    def Clear(self):
        logging.info("EPD Clear (simulated)")
        return 0
    
    def display(self, image_buffer):
        logging.info("EPD display update (simulated)")
        return 0
    
    def sleep(self):
        logging.info("EPD sleep (simulated)")
        return 0
    
    def getbuffer(self, image):
        logging.info("EPD getbuffer (simulated)")
        width, height = image.size
        buffer_size = ((width + 7) // 8) * height
        return bytearray([0xFF] * buffer_size)

# Create a module function to get the appropriate EPD class
def get_epd_class(epd_name):
    """Returns a simulated EPD class based on the name"""
    if epd_name == "epd2in13_V3":
        return EPDSimulator(width=122, height=250)
    # Add more display types as needed
    return EPDSimulator() 