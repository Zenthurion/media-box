#!/usr/bin/python
import sys
import os
import time
import logging
from PIL import Image, ImageDraw, ImageFont

# Setup paths
lib_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib')
if os.path.exists(lib_dir):
    sys.path.append(lib_dir)

# Set HAT mode
os.environ['WAVESHARE_HAT'] = '1'

# Configure logging
logging.basicConfig(level=logging.DEBUG)

try:
    # Import the library
    from waveshare_epd import epd2in13_V4
    
    logging.info("Starting e-Paper V4 test")
    
    # Initialize display
    epd = epd2in13_V4.EPD()
    logging.info("Init and Clear")
    epd.init()
    epd.Clear(0xFF)  # Explicitly clear with white
    
    # Drawing test pattern
    logging.info("Drawing test pattern")
    
    # Re-initialize before drawing
    epd.init()
    
    # Create a new image with white background
    image = Image.new('1', (epd.height, epd.width), 255)
    draw = ImageDraw.Draw(image)
    
    # Draw basic shapes
    draw.rectangle([(0,0), (50,50)], outline=0)  # Empty rectangle
    draw.rectangle([(55,0), (100,50)], fill=0)    # Filled rectangle
    
    # Draw lines
    draw.line([(0,0), (50,50)], fill=0, width=1)  # Diagonal line
    draw.line([(0,50), (50,0)], fill=0, width=1)  # Diagonal line
    
    # Try with a default font since we don't have their custom font
    try:
        # Try system font if available
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    except IOError:
        # Fall back to default font if system font isn't available
        font = ImageFont.load_default()
    
    # Add text
    draw.text((110, 60), 'E-Paper Test', font=font, fill=0)
    draw.text((110, 80), 'Waveshare V4', font=font, fill=0)
    
    # Display the buffer
    logging.info("Displaying image...")
    epd.display(epd.getbuffer(image))
    
    # Wait for image to display
    time.sleep(2)
    
    # Clock demo for partial updates
    logging.info("Showing clock demo...")
    time_image = Image.new('1', (epd.height, epd.width), 255)
    time_draw = ImageDraw.Draw(time_image)
    
    # Set up base image
    epd.displayPartBaseImage(epd.getbuffer(time_image))
    
    # Update time 5 times
    for i in range(5):
        time_draw.rectangle((110, 40, 220, 70), fill=255)  # Clear previous time
        time_draw.text((110, 40), time.strftime('%H:%M:%S'), font=font, fill=0)
        epd.displayPartial(epd.getbuffer(time_image))
        time.sleep(1)
    
    # Final cleanup
    logging.info("Cleaning up...")
    epd.init()
    epd.Clear(0xFF)
    
    logging.info("Going to sleep...")
    epd.sleep()
    
except Exception as e:
    logging.error(f"Error: {e}")
    logging.error(traceback.format_exc())
    
finally:
    # Ensure proper cleanup
    logging.info("Cleanup")
    try:
        epd2in13_V4.epdconfig.module_exit(cleanup=True)
    except:
        pass 