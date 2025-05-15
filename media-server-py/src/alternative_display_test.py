#!/usr/bin/python
import sys
import os
import time
from PIL import Image, ImageDraw, ImageFont

# Try alternative display models
display_models = [
    "epd2in13", 
    "epd2in13_V2",
    "epd2in13_V3",
    "epd2in13bc", 
    "epd2in13d"
]

# Add lib directory to path
lib_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib')
if os.path.exists(lib_dir):
    sys.path.append(lib_dir)

# Set HAT pins
os.environ['WAVESHARE_HAT'] = '1'

for model in display_models:
    print(f"\nTrying model: {model}")
    try:
        # Dynamic import based on model name
        module = __import__(f"waveshare_epd.{model}", fromlist=["waveshare_epd"])
        
        # Initialize display
        epd = module.EPD()
        epd.init()
        epd.Clear()
        
        # Create simple test image
        image = Image.new('1', (epd.width, epd.height), 255)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, epd.width-1, epd.height-1), outline=0, width=3)
        draw.text((10, 10), f'Model: {model}', fill=0)
        
        # Display and wait
        buffer = epd.getbuffer(image)
        epd.display(buffer)
        print(f"Test image sent to {model}. Check if visible!")
        time.sleep(10)
        
    except Exception as e:
        print(f"Error with {model}: {e}")
        continue 