#!/usr/bin/python
import spidev
import RPi.GPIO as GPIO
import time

# Check GPIO access
print("Testing GPIO...")
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)  # Using RST pin for test
GPIO.output(17, GPIO.HIGH)
time.sleep(1)
GPIO.output(17, GPIO.LOW)
time.sleep(1)
GPIO.output(17, GPIO.HIGH)
print("GPIO test complete")

# Check SPI access
print("Testing SPI...")
try:
    spi = spidev.SpiDev()
    spi.open(0, 0)  # Bus 0, Device 0
    spi.max_speed_hz = 1000000
    print("SPI connection established")
    
    # Try sending some data
    response = spi.xfer2([0x00])
    print(f"SPI response: {response}")
    
    spi.close()
    print("SPI test complete")
except Exception as e:
    print(f"SPI error: {e}")

GPIO.cleanup()