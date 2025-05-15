#!/usr/bin/python
import RPi.GPIO as GPIO
import spidev
import time

# Configuration for 2.13" V3 display
RST_PIN = 27
DC_PIN = 22
CS_PIN = 8
BUSY_PIN = 17

# Basic low-level test with enhanced debugging
try:
    # Setup GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Check initial pin states
    GPIO.setup(BUSY_PIN, GPIO.IN)
    busy_initial = GPIO.input(BUSY_PIN)
    print(f"Initial BUSY pin state: {busy_initial}")
    
    # Setup other pins
    GPIO.setup(RST_PIN, GPIO.OUT)
    GPIO.setup(DC_PIN, GPIO.OUT)
    GPIO.setup(CS_PIN, GPIO.OUT)
    
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
    
    # Check BUSY pin after reset
    busy_after_reset = GPIO.input(BUSY_PIN)
    print(f"BUSY pin state after reset: {busy_after_reset}")
    
    # Send a simple command to display
    print("Sending command to display...")
    
    # Power on command
    GPIO.output(DC_PIN, GPIO.LOW)  # Command mode
    GPIO.output(CS_PIN, GPIO.LOW)  # Select device
    spi.writebytes([0x04])         # Power ON command
    GPIO.output(CS_PIN, GPIO.HIGH) # Deselect device
    
    # Check BUSY pin after command
    busy_after_cmd = GPIO.input(BUSY_PIN)
    print(f"BUSY pin state after command: {busy_after_cmd}")
    
    # Wait for display with timeout (5 seconds max)
    print("Waiting for display to be ready (with 5-second timeout)...")
    timeout = time.time() + 5  # 5 second timeout
    
    while GPIO.input(BUSY_PIN) == 0 and time.time() < timeout:
        print("BUSY pin is LOW, waiting...")
        time.sleep(0.5)
    
    final_busy = GPIO.input(BUSY_PIN)
    if final_busy == 0:
        print("TIMEOUT: BUSY pin never went HIGH - display not responding")
    else:
        print("SUCCESS: BUSY pin went HIGH - display responded")
    
    print(f"Final BUSY pin state: {final_busy}")
    
    # Try a different reset/init sequence
    print("\nAttempting alternative init sequence...")
    
    # Hard reset
    GPIO.output(RST_PIN, GPIO.LOW)
    time.sleep(1.0)  # longer reset
    GPIO.output(RST_PIN, GPIO.HIGH)
    time.sleep(1.0)  # longer wait
    
    # Send reset command (many e-ink displays use 0x12)
    GPIO.output(DC_PIN, GPIO.LOW)  # Command mode
    GPIO.output(CS_PIN, GPIO.LOW)  # Select device
    spi.writebytes([0x12])         # SWRESET command
    GPIO.output(CS_PIN, GPIO.HIGH) # Deselect device
    
    time.sleep(1.0)
    busy_after_alt = GPIO.input(BUSY_PIN)
    print(f"BUSY pin after alternative init: {busy_after_alt}")
    
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