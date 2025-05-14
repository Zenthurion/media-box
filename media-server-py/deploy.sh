#!/bin/bash

# Configuration
PI_HOST="pi@192.168.50.88"
PROJECT_NAME="media-box"
SERVICE_NAME="media-box.service"

# Build for Raspberry Pi 2 architecture
echo "Building Docker image for Raspberry Pi..."
docker buildx build --platform linux/arm/v7 -t $PROJECT_NAME:latest .

# Save the image
echo "Saving Docker image..."
docker save $PROJECT_NAME:latest > $PROJECT_NAME.tar

# Copy files to Raspberry Pi
echo "Copying files to Raspberry Pi..."
scp $PROJECT_NAME.tar $PI_HOST:~/
scp systemd/$SERVICE_NAME $PI_HOST:~/

# Execute remote commands
echo "Setting up on Raspberry Pi..."
ssh $PI_HOST << 'EOF'
    # Load the Docker image
    docker load < media-box.tar
    
    # Copy service file to systemd
    sudo mv media-box.service /etc/systemd/system/
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable media-box
    sudo systemctl restart media-box
    
    # Cleanup
    rm media-box.tar
EOF

# Cleanup local files
rm $PROJECT_NAME.tar

echo "Deployment complete!" 