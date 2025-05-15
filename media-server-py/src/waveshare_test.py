#!/usr/bin/python
import sys
import os
import time
from PIL import Image, ImageDraw, ImageFont

# Add system path to Waveshare library
sys.path.append("/home/markus/Projects/media-box/media-server-py/lib")

# Set HAT mode
os.environ['WAVESHARE_HAT'] = '1'

try:
    # Import the library that worked in the official example
    from waveshare_epd import epd2in13_V3
    
    epd = epd2in13_V3.EPD()
    print("Initializing e-ink display...")
    epd.init()
    print("Clearing display...")
    epd.Clear()
    
    # Drawing on the image
    print("Creating test image...")
    font18 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    font24 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
    
    image = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the image with white
    draw = ImageDraw.Draw(image)
    
    draw.rectangle((0, 0, epd.height, epd.width), outline=0)
    draw.text((10, 10), 'Working Example!', font=font24, fill=0)
    draw.text((10, 40), 'Powered by Waveshare', font=font18, fill=0)
    draw.line((10, 60, epd.height-10, 60), fill=0)
    draw.line((10, 80, epd.height-10, 80), fill=0)
    draw.text((10, 85), 'Display is functional!', font=font18, fill=0)
    
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