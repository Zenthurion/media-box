#!/usr/bin/python
import RPi.GPIO as GPIO
import spidev
import time

# Configuration for 2.13" V3 display
RST_PIN = 27
DC_PIN = 22
CS_PIN = 8
BUSY_PIN = 17

# Basic low-level test
try:
    # Setup GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RST_PIN, GPIO.OUT)
    GPIO.setup(DC_PIN, GPIO.OUT)
    GPIO.setup(CS_PIN, GPIO.OUT)
    GPIO.setup(BUSY_PIN, GPIO.IN)
    
    # Initialize SPI
    spi = spidev.SpiDev()
    spi.open(0, 0)  # Bus 0, Device 0
    spi.max_speed_hz = 4000000
    spi.mode = 0
    
    # Reset the display
    print("Resetting display...")
    GPIO.output(RST_PIN, GPIO.LOW)
    time.sleep(0.2)
    GPIO.output(RST_PIN, GPIO.HIGH)
    time.sleep(0.2)
    
    # Send a simple command to display
    print("Sending command to display...")
    
    # Power on command
    GPIO.output(DC_PIN, GPIO.LOW)  # Command mode
    GPIO.output(CS_PIN, GPIO.LOW)  # Select device
    spi.writebytes([0x04])         # Power ON command
    GPIO.output(CS_PIN, GPIO.HIGH) # Deselect device
    
    # Wait for display to be ready
    print("Waiting for display to be ready...")
    while GPIO.input(BUSY_PIN) == 0:
        time.sleep(0.1)
    
    print("Display should have received power on command")
    
    # Clean up
    GPIO.cleanup([RST_PIN, DC_PIN, CS_PIN, BUSY_PIN])
    spi.close()
    
except Exception as e:
    print(f"Error: {e}")
    try:
        GPIO.cleanup([RST_PIN, DC_PIN, CS_PIN, BUSY_PIN])
        spi.close()
    except:
        pass 