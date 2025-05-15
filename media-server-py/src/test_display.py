#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import logging
import time
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.DEBUG)

print("Testing e-ink display for Raspberry Pi HAT variant")

# Modify pin definitions for HAT variant (before importing waveshare_epd)
os.environ['WAVESHARE_HAT'] = '1'  # Signal we're using HAT variant

try:
    # Add lib directory to path
    lib_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib')
    if os.path.exists(lib_dir):
        sys.path.append(lib_dir)
        print(f"Added lib directory to path: {lib_dir}")

    from waveshare_epd import epd2in13_V3
    print("Successfully imported Waveshare library")
    
    try:
        epd = epd2in13_V3.EPD()
        logging.info("Initializing...")
        
        # Print the currently used pins
        print(f"Using pins: RST={epd2in13_V3.epdconfig.RST_PIN}, DC={epd2in13_V3.epdconfig.DC_PIN}, CS={epd2in13_V3.epdconfig.CS_PIN}, BUSY={epd2in13_V3.epdconfig.BUSY_PIN}")
        
        # Test different initialization modes
        logging.info("Initializing in FULL_UPDATE mode")
        epd.init(epd.FULL_UPDATE)
        logging.info("Clear...")
        epd.Clear()
        time.sleep(1)
        
        # Print dimensions
        logging.info(f"Display dimensions: {epd.width}x{epd.height}")
        
        # Create simple test image
        logging.info("Creating test image...")
        image = Image.new('1', (epd.width, epd.height), 255)  # 255: white, 0: black
        draw = ImageDraw.Draw(image)
        
        # Draw black frame
        draw.rectangle((0, 0, epd.width-1, epd.height-1), outline=0, width=3)
        
        # Draw diagonal lines
        draw.line((0, 0, epd.width-1, epd.height-1), fill=0, width=3)
        draw.line((0, epd.height-1, epd.width-1, 0), fill=0, width=3)
        
        # Try to use a system font
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 24)
        else:
            font = ImageFont.load_default()
        
        # Draw text
        draw.text((epd.width//4, epd.height//4), 'TEST', font=font, fill=0)
        
        # Try all 4 rotations one by one
        for rotation in [0, 90, 180, 270]:
            logging.info(f"Trying rotation {rotation}...")
            rotated = image.rotate(rotation)
            
            # Save debug image
            rotated.save(f'/tmp/eink_rotate_{rotation}.png')
            
            # Update display
            epd.display(epd.getbuffer(rotated))
            logging.info(f"Updated display with rotation {rotation}")
            time.sleep(5)  # Wait 5 seconds between rotations
        
        logging.info("Done!")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        raise
        
except ImportError as e:
    logging.error(f"Error importing library: {e}")
    logging.error("Make sure the waveshare_epd library is installed") 