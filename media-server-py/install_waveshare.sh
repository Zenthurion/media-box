#!/bin/bash
# Script to install Waveshare e-Paper display library

echo "Installing Waveshare e-Paper Display Library..."

# Create a temporary directory
mkdir -p /tmp/waveshare_setup
cd /tmp/waveshare_setup

# Clone the repository
git clone https://github.com/waveshare/e-Paper.git
cd e-Paper/RaspberryPi_JetsonNano/python

# Install the library
sudo python3 setup.py install

# Cleanup
cd /
rm -rf /tmp/waveshare_setup

echo "Waveshare e-Paper library installation complete!" 