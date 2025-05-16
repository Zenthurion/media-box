#!/usr/bin/env python3
"""
Simple script to test e-ink display with logo
"""
import os
import sys
import logging
from PIL import Image
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the lib directory to path
lib_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib')
sys.path.append(lib_dir)

try:
    from waveshare_epd import epd2in13_V4
    logging.info("Successfully imported waveshare library")
except ImportError as e:
    logging.error(f"Failed to import waveshare library: {e}")
    sys.exit(1)

def main():
    """Test displaying logo on e-ink screen"""
    logging.info("E-ink display test starting")
    
    # Initialize display
    try:
        epd = epd2in13_V4.EPD()
        logging.info("Initializing display...")
        
        # Define fallback values if needed
        FULL_UPDATE = getattr(epd, 'FULL_UPDATE', 0)
        PART_UPDATE = getattr(epd, 'PART_UPDATE', 1)
        
        logging.info(f"Using update modes - FULL: {FULL_UPDATE}, PART: {PART_UPDATE}")
        
        epd.init(FULL_UPDATE)
        epd.Clear()
        
        # Display dimensions
        width = epd.height  # Note the width/height swap for proper orientation
        height = epd.width
        logging.info(f"Display size: {width}x{height}")
        
        # Try to find logo image
        possible_paths = [
            Path("/app/logo.png"),
            Path(os.path.dirname(os.path.abspath(__file__))) / "logo.png",
            Path("logo.png"),
        ]
        
        for path in possible_paths:
            logging.info(f"Checking for logo at: {path} (exists: {path.exists()})")
        
        logo_path = None
        for path in possible_paths:
            if path.exists():
                logo_path = path
                break
        
        if logo_path:
            logging.info(f"Found logo at {logo_path}")
            logo_img = Image.open(logo_path)
            logging.info(f"Logo dimensions: {logo_img.size}")
            
            # Resize if needed
            if logo_img.size != (width, height):
                logo_img = logo_img.resize((width, height), Image.LANCZOS)
                logging.info(f"Resized to {width}x{height}")
            
            # Convert to 1-bit
            if logo_img.mode != '1':
                logo_img = logo_img.convert('1')
                logging.info("Converted to 1-bit mode")
            
            # Display the image
            logging.info("Sending to display...")
            buffer = epd.getbuffer(logo_img)
            epd.display(buffer)
            logging.info("Image displayed")
            
        else:
            logging.error("No logo found, drawing test pattern")
            # Draw test pattern
            img = Image.new('1', (width, height), 255)
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.rectangle((0, 0, width-1, height-1), outline=0, width=2)
            draw.line((0, 0, width-1, height-1), fill=0, width=2)
            draw.line((0, height-1, width-1, 0), fill=0, width=2)
            draw.text((width//2 - 30, height//2 - 10), "TEST IMAGE", fill=0)
            
            # Display the test image
            buffer = epd.getbuffer(img)
            epd.display(buffer)
            logging.info("Test pattern displayed")
        
        # Sleep for 30 seconds to let the image display
        import time
        logging.info("Waiting 30 seconds...")
        time.sleep(30)
        
        # Put display to sleep
        logging.info("Putting display to sleep")
        epd.sleep()
        logging.info("Test completed")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 