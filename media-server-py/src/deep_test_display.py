#!/usr/bin/python
import sys
import os
import logging
import time
import subprocess
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.DEBUG)

# Verify SPI is enabled
print("Checking SPI devices...")
try:
    result = subprocess.run(['ls', '-la', '/dev/spi*'], capture_output=True, text=True)
    print(f"SPI devices: {result.stdout}")
    if not result.stdout:
        print("WARNING: No SPI devices found! Make sure SPI is enabled.")
except:
    print("WARNING: Failed to check SPI devices")

# Test different pin configurations
pin_configs = [
    # Common HAT pins
    {'name': 'Standard HAT', 'RST': 27, 'DC': 22, 'CS': 8, 'BUSY': 17},
    # Alternative HAT pins
    {'name': 'Alt HAT 1', 'RST': 17, 'DC': 25, 'CS': 8, 'BUSY': 24},
    {'name': 'Alt HAT 2', 'RST': 5, 'DC': 6, 'CS': 8, 'BUSY': 13},
    {'name': 'Alt HAT 3', 'RST': 17, 'DC': 27, 'CS': 8, 'BUSY': 22},
]

try:
    # Add lib directory to path
    lib_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib')
    if os.path.exists(lib_dir):
        sys.path.append(lib_dir)
        print(f"Added lib directory to path: {lib_dir}")

    print("Testing multiple pin configurations...")
    for config in pin_configs:
        print(f"\nTrying pin config: {config['name']}")
        print(f"RST={config['RST']}, DC={config['DC']}, CS={config['CS']}, BUSY={config['BUSY']}")
        
        # Set pins for this test
        os.environ['WAVESHARE_RST_PIN'] = str(config['RST'])
        os.environ['WAVESHARE_DC_PIN'] = str(config['DC'])
        os.environ['WAVESHARE_CS_PIN'] = str(config['CS'])
        os.environ['WAVESHARE_BUSY_PIN'] = str(config['BUSY'])
        os.environ['WAVESHARE_CUSTOM_PINS'] = '1'
        
        try:
            # Reimport to get new config
            from waveshare_epd import epd2in13_V3
            
            # Create display instance
            epd = epd2in13_V3.EPD()
            epd.init(epd.FULL_UPDATE)
            epd.Clear()
            
            # Draw a simple test image
            print("Drawing test image...")
            image = Image.new('1', (epd.width, epd.height), 255)
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, epd.width-1, epd.height-1), outline=0, width=5)
            draw.text((10, 10), f'Test: {config["name"]}', fill=0)
            
            # Display and wait to see if it appears
            epd.display(epd.getbuffer(image))
            print(f"Displayed test for {config['name']}. Check if visible on display.")
            print("Wait 10 seconds before trying next config...")
            time.sleep(10)
            
        except Exception as e:
            print(f"Error with {config['name']} config: {e}")
            continue
            
except Exception as e:
    print(f"General error: {e}") 