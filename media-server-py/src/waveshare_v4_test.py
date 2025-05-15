#!/usr/bin/python
import sys
import os
import time
from PIL import Image, ImageDraw, ImageFont

# Add path to Waveshare library
lib_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib')
if os.path.exists(lib_dir):
    sys.path.append(lib_dir)

# Set HAT mode
os.environ['WAVESHARE_HAT'] = '1'

try:
    # Import the V4 library specifically
    from waveshare_epd import epd2in13_V4
    
    epd = epd2in13_V4.EPD()
    print("Initializing e-ink display (V4)...")
    epd.init()
    print("Clearing display...")
    epd.Clear()
    
    # Drawing on the image
    print("Creating test image...")
    font18 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    font24 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
    
    # Create image with the correct dimensions for V4
    image = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the image with white
    draw = ImageDraw.Draw(image)
    
    draw.rectangle((0, 0, epd.height, epd.width), outline=0)
    draw.text((10, 10), 'V4 Display Test', font=font24, fill=0)
    draw.text((10, 40), 'Using V4 Library', font=font18, fill=0)
    draw.line((10, 60, epd.height-10, 60), fill=0)
    draw.text((10, 85), 'This should work!', font=font18, fill=0)
    
    # Display the image
    print("Displaying image...")
    epd.display(epd.getbuffer(image))
    print("Done!")
    
    time.sleep(2)
    
    # Sleep mode
    print("Putting display to sleep...")
    epd.sleep()
    
except Exception as e:
    print(f"Error: {e}") 