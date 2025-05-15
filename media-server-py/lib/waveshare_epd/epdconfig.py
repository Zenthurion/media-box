# -*- coding:utf-8 -*-

import os
import logging
import time

# Check if we're using HAT variant
HAT_VARIANT = os.environ.get('WAVESHARE_HAT', '0') == '1'
if HAT_VARIANT:
    logging.info("Using pin configuration for HAT variant")
    # Pin definition for HAT variant
    RST_PIN         = 27  # Pin 13 on HAT (adjust if your HAT uses different pins)
    DC_PIN          = 22  # Pin 15 on HAT
    CS_PIN          = 8   # Pin 24 on HAT
    BUSY_PIN        = 17  # Pin 11 on HAT
else:
    # Standard pin definition
    RST_PIN         = 17
    DC_PIN          = 25
    CS_PIN          = 8
    BUSY_PIN        = 24

# Support custom pin definitions from environment variables
CUSTOM_PINS = os.environ.get('WAVESHARE_CUSTOM_PINS', '0') == '1'
if CUSTOM_PINS:
    RST_PIN = int(os.environ.get('WAVESHARE_RST_PIN', '17'))
    DC_PIN = int(os.environ.get('WAVESHARE_DC_PIN', '25'))
    CS_PIN = int(os.environ.get('WAVESHARE_CS_PIN', '8'))
    BUSY_PIN = int(os.environ.get('WAVESHARE_BUSY_PIN', '24'))
    logging.info(f"Using custom pins: RST={RST_PIN}, DC={DC_PIN}, CS={CS_PIN}, BUSY={BUSY_PIN}")

# Only use WAVESHARE_SIMULATOR env var to determine simulator mode
SIMULATOR = os.environ.get('WAVESHARE_SIMULATOR', '0') == '1'
logging.info(f"Waveshare config initialized (simulator mode: {SIMULATOR})")

# SPI device, bus = 0, device = 0
SPI_PORT        = 0
SPI_DEVICE      = 0

# GPIO modules and SPI module
if not SIMULATOR:
    try:
        import RPi.GPIO as GPIO
        import spidev
        GPIO_AVAILABLE = True
        SPI_AVAILABLE = True
    except ImportError:
        GPIO_AVAILABLE = False
        SPI_AVAILABLE = False
        logging.warning("RPi.GPIO or spidev module not found, running in simulator mode")
else:
    GPIO_AVAILABLE = False
    SPI_AVAILABLE = False
    logging.info("Running in simulator mode")

# Initialize GPIO and SPI
GPIO_INITIALIZED = False
SPI_INITIALIZED = False
spi = None

def epd_digital_write(pin, value):
    if GPIO_AVAILABLE:
        GPIO.output(pin, value)
    else:
        # In simulator mode, just log the operation
        logging.debug(f"GPIO write: pin={pin}, value={value}")

def epd_digital_read(pin):
    if GPIO_AVAILABLE:
        return GPIO.input(pin)
    else:
        # In simulator mode, always return 1 (not busy)
        return 1

def epd_delay_ms(delaytime):
    time.sleep(delaytime / 1000.0)

def spi_transfer(data):
    if SPI_AVAILABLE:
        spi.writebytes(data)
    else:
        # In simulator mode, just log the operation
        logging.debug(f"SPI transfer: {data}")

def module_init():
    global GPIO_INITIALIZED, SPI_INITIALIZED, spi
    
    if not SIMULATOR and not GPIO_INITIALIZED and GPIO_AVAILABLE:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(RST_PIN, GPIO.OUT)
        GPIO.setup(DC_PIN, GPIO.OUT)
        GPIO.setup(CS_PIN, GPIO.OUT)
        GPIO.setup(BUSY_PIN, GPIO.IN)
        
        # SPI initialization
        if not SPI_INITIALIZED and SPI_AVAILABLE:
            spi = spidev.SpiDev()
            spi.open(SPI_PORT, SPI_DEVICE)
            spi.max_speed_hz = 4000000
            spi.mode = 0b00
            SPI_INITIALIZED = True
            
        GPIO_INITIALIZED = True
        return 0
    else:
        # Already initialized or in simulator mode
        return 0

def module_exit():
    global GPIO_INITIALIZED, SPI_INITIALIZED, spi
    
    if not SIMULATOR:
        if GPIO_INITIALIZED and GPIO_AVAILABLE:
            logging.debug("Cleanup GPIO")
            GPIO.cleanup([RST_PIN, DC_PIN, CS_PIN, BUSY_PIN])
            GPIO_INITIALIZED = False
            
        if SPI_INITIALIZED and SPI_AVAILABLE:
            logging.debug("Close SPI")
            spi.close()
            SPI_INITIALIZED = False
    
    return 0

# Define functions with the names used in the EPD modules
digital_write = epd_digital_write
digital_read = epd_digital_read
delay_ms = epd_delay_ms
spi_writebyte = spi_transfer

def spi_writebyte2(data):
    """Compatibility function for spi_writebyte2"""
    return spi_transfer(data)

# Make it available at module level
spi_writebyte2 = spi_writebyte2 