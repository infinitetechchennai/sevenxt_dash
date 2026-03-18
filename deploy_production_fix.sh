#!/bin/bash

# Production Fix Deployment Script
# Run this on your EC2 Ubuntu server

set -e  # Exit on error

echo "=================================="
echo "Production Fix Deployment Script"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="/home/ubuntu/backend"
APP_USER="ubuntu"
SERVICE_NAME="backend"  # Change this to your systemd service name

echo -e "${YELLOW}Step 1: Navigating to backend directory${NC}"
cd $BACKEND_DIR || { echo -e "${RED}Failed to navigate to $BACKEND_DIR${NC}"; exit 1; }
echo -e "${GREEN}✓ Current directory: $(pwd)${NC}"
echo ""

echo -e "${YELLOW}Step 2: Creating backup${NC}"
BACKUP_FILE="app/modules/orders/routes.py.backup.$(date +%Y%m%d_%H%M%S)"
cp app/modules/orders/routes.py $BACKUP_FILE
echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
echo ""

echo -e "${YELLOW}Step 3: Creating required directories${NC}"
mkdir -p uploads/awb
mkdir -p uploads/invoice_labels
mkdir -p uploads/invoices
mkdir -p uploads/return_awb
mkdir -p static/temp
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

echo -e "${YELLOW}Step 4: Setting permissions${NC}"
chown -R $APP_USER:$APP_USER uploads/
chown -R $APP_USER:$APP_USER static/
chmod -R 755 uploads/
chmod -R 755 static/
echo -e "${GREEN}✓ Permissions set${NC}"
echo ""

echo -e "${YELLOW}Step 5: Checking file existence${NC}"
AWB_COUNT=$(find uploads/awb -name "*.pdf" -type f 2>/dev/null | wc -l)
echo -e "${GREEN}✓ Found $AWB_COUNT AWB label files${NC}"
echo ""

echo -e "${YELLOW}Step 6: Pulling latest code from Git${NC}"
if [ -d ".git" ]; then
    git pull origin main || echo -e "${YELLOW}⚠ Git pull failed or not configured${NC}"
else
    echo -e "${YELLOW}⚠ Not a git repository. Please upload routes.py manually.${NC}"
fi
echo ""

echo -e "${YELLOW}Step 7: Detecting service manager${NC}"
if systemctl is-active --quiet $SERVICE_NAME 2>/dev/null; then
    echo -e "${GREEN}✓ Detected systemd service: $SERVICE_NAME${NC}"
    echo -e "${YELLOW}Restarting service...${NC}"
    sudo systemctl restart $SERVICE_NAME
    sleep 2
    sudo systemctl status $SERVICE_NAME --no-pager -l
elif command -v pm2 &> /dev/null; then
    echo -e "${GREEN}✓ Detected PM2${NC}"
    echo -e "${YELLOW}Restarting PM2 process...${NC}"
    pm2 restart $SERVICE_NAME || pm2 restart all
    pm2 logs $SERVICE_NAME --lines 20 --nostream
elif command -v supervisorctl &> /dev/null; then
    echo -e "${GREEN}✓ Detected Supervisor${NC}"
    echo -e "${YELLOW}Restarting supervisor process...${NC}"
    sudo supervisorctl restart $SERVICE_NAME
    sudo supervisorctl status $SERVICE_NAME
else
    echo -e "${RED}✗ Could not detect service manager${NC}"
    echo -e "${YELLOW}Please restart your backend manually:${NC}"
    echo "  ps aux | grep uvicorn"
    echo "  kill -9 <PID>"
    echo "  cd $BACKEND_DIR && uvicorn app.main:app --host 0.0.0.0 --port 8000 &"
fi
echo ""

echo -e "${YELLOW}Step 8: Verification${NC}"
echo "Checking if backend is responding..."
sleep 3
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running!${NC}"
else
    echo -e "${RED}✗ Backend might not be running. Check logs.${NC}"
fi
echo ""

echo -e "${GREEN}=================================="
echo "Deployment Complete!"
echo "==================================${NC}"
echo ""
echo "Next steps:"
echo "1. Check logs: tail -f /var/log/backend.log"
echo "2. Test bulk download from frontend"
echo "3. Monitor for 'Checking for AWB label at:' messages"
echo ""
echo "Rollback command (if needed):"
echo "  cp $BACKUP_FILE app/modules/orders/routes.py"
echo "  sudo systemctl restart $SERVICE_NAME"
echo ""
