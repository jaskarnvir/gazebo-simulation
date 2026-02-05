#!/bin/bash

# Configuration - REPLACE THESE WITH YOUR VALUES
REMOTE_USER="YOUR_SSH_USERNAME" 
REMOTE_IP="34.172.64.198"
# REMOTE_KEY_PATH="path/to/your/private/key" # Uncomment if needed, e.g. ~/.ssh/google_compute_engine

echo "🚀 Deploying backend to $REMOTE_IP..."

# 1. Upload the backend code
echo "📦 Uploading files..."
# We exclude __pycache__ and venv to save time and bandwidth
rsync -avz --exclude '__pycache__' --exclude 'venv' --exclude '*.db' ./backend/ $REMOTE_USER@$REMOTE_IP:~/backend/

# 2. Restart the server
# Adjust the restart command based on how you are running it (systemd, docker, or simple nohup)
echo "🔄 Restarting server service..."
ssh $REMOTE_USER@$REMOTE_IP "cd ~/backend && sudo pkill -f uvicorn; nohup uvicorn main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &"

echo "✅ Deployment complete!"
