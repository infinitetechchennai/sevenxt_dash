# Production Deployment Fix Guide
# Issue: Bulk AWB/Invoice Download Returns 404 - Files Not Found

## Problem Summary
The bulk download feature works locally but fails in production because:
- Code uses `os.getcwd()` which returns different paths in dev vs production
- In production, the current working directory may not be `/home/ubuntu/backend/`
- Files exist but can't be found due to incorrect path construction

## Code Changes Made

### 1. Added BASE_DIR constant (routes.py)
```python
from pathlib import Path

# Define base directory (absolute path to backend folder)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
```

### 2. Updated bulk AWB download (routes.py ~line 550)
```python
# OLD: full_path = os.path.join(os.getcwd(), label_path)
# NEW: full_path = os.path.join(BASE_DIR, label_path)
```

### 3. Updated bulk invoice download (routes.py ~line 626)
```python
# OLD: output_dir = os.path.join("uploads", "invoice_labels")
# NEW: output_dir = os.path.join(BASE_DIR, "uploads", "invoice_labels")
```

### 4. Updated single invoice generation (routes.py ~line 718)
```python
# OLD: output_dir = os.path.join("uploads", "invoice_labels")
# NEW: output_dir = os.path.join(BASE_DIR, "uploads", "invoice_labels")
```

---

## Ubuntu Production Deployment Steps

### Step 1: Connect to EC2
```bash
ssh -i your-key.pem ubuntu@13.232.178.156
```

### Step 2: Navigate to Backend Directory
```bash
cd /home/ubuntu/backend
```

### Step 3: Backup Current Code
```bash
# Create backup
cp app/modules/orders/routes.py app/modules/orders/routes.py.backup.$(date +%Y%m%d_%H%M%S)
```

### Step 4: Pull Latest Code from Git
```bash
# If using git
git pull origin main

# OR manually upload the updated routes.py file using:
# scp -i your-key.pem routes.py ubuntu@13.232.178.156:/home/ubuntu/backend/app/modules/orders/
```

### Step 5: Verify File Permissions
```bash
# Ensure uploads directory exists and has correct permissions
mkdir -p /home/ubuntu/backend/uploads/awb
mkdir -p /home/ubuntu/backend/uploads/invoice_labels
mkdir -p /home/ubuntu/backend/uploads/invoices
mkdir -p /home/ubuntu/backend/static/temp

# Set ownership (replace 'ubuntu' with your app user if different)
sudo chown -R ubuntu:ubuntu /home/ubuntu/backend/uploads
sudo chown -R ubuntu:ubuntu /home/ubuntu/backend/static

# Set permissions
chmod -R 755 /home/ubuntu/backend/uploads
chmod -R 755 /home/ubuntu/backend/static
```

### Step 6: Restart Backend Service

#### If using systemd:
```bash
sudo systemctl restart your-backend-service
sudo systemctl status your-backend-service
```

#### If using PM2:
```bash
pm2 restart backend
pm2 logs backend --lines 50
```

#### If using supervisor:
```bash
sudo supervisorctl restart backend
sudo supervisorctl status backend
```

#### If running manually with uvicorn:
```bash
# Find and kill existing process
ps aux | grep uvicorn
kill -9 <PID>

# Restart
cd /home/ubuntu/backend
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /var/log/backend.log 2>&1 &
```

### Step 7: Verify the Fix
```bash
# Check if files exist
ls -la /home/ubuntu/backend/uploads/awb/

# Check backend logs
tail -f /var/log/backend.log
# OR
journalctl -u your-backend-service -f
# OR
pm2 logs backend
```

### Step 8: Test from Frontend
1. Go to your production frontend: http://13.232.178.156
2. Select orders with AWB labels
3. Click "Bulk Download AWB"
4. Should download successfully!

---

## Verification Commands

### Check Current Working Directory
```bash
# Add this temporarily to your code to debug:
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"BASE_DIR: {BASE_DIR}")
```

### Check File Existence
```bash
# List all AWB files
find /home/ubuntu/backend/uploads -name "*.pdf" -type f

# Check specific AWB
ls -la /home/ubuntu/backend/uploads/awb/awb_84927910001234.pdf
```

### Check Process Working Directory
```bash
# Find uvicorn process
ps aux | grep uvicorn

# Check its working directory (replace PID)
pwdx <PID>
```

---

## Troubleshooting

### Issue: Permission Denied
```bash
# Fix ownership
sudo chown -R ubuntu:ubuntu /home/ubuntu/backend/uploads
sudo chmod -R 755 /home/ubuntu/backend/uploads
```

### Issue: Module Not Found
```bash
# Reinstall dependencies
cd /home/ubuntu/backend
source venv/bin/activate  # if using venv
pip install -r requirements.txt
```

### Issue: Service Won't Restart
```bash
# Check logs for errors
sudo journalctl -u your-backend-service -n 100 --no-pager

# Check if port is in use
sudo netstat -tulpn | grep 8000
```

### Issue: Still Getting 404
```bash
# Check backend logs for the new debug message
tail -f /var/log/backend.log | grep "Checking for AWB label"

# This will show the exact path being checked
```

---

## Quick Test Script

Create a test file to verify paths:
```bash
cat > /home/ubuntu/backend/test_paths.py << 'EOF'
from pathlib import Path
import os

# Simulate the code
BASE_DIR = Path(__file__).resolve().parent
print(f"BASE_DIR: {BASE_DIR}")
print(f"os.getcwd(): {os.getcwd()}")

label_path = "/uploads/awb/awb_84927910001234.pdf"
if label_path.startswith('/'):
    label_path = label_path[1:]

full_path = os.path.join(BASE_DIR, label_path)
print(f"Full path: {full_path}")
print(f"File exists: {os.path.exists(full_path)}")
EOF

python3 /home/ubuntu/backend/test_paths.py
```

---

## Rollback Plan (If Something Goes Wrong)

```bash
# Restore backup
cd /home/ubuntu/backend
cp app/modules/orders/routes.py.backup.YYYYMMDD_HHMMSS app/modules/orders/routes.py

# Restart service
sudo systemctl restart your-backend-service
```

---

## Expected Log Output (After Fix)

```
INFO: Checking for AWB label at: /home/ubuntu/backend/uploads/awb/awb_84927910001234.pdf
INFO: Added ORD-123 label to merge
INFO: Checking for AWB label at: /home/ubuntu/backend/uploads/awb/awb_84927910001223.pdf
INFO: Added ORD-124 label to merge
INFO: Created merged PDF with 2 labels: static/temp/AWB_Labels_Bulk_20260120_160500.pdf
```

---

## Summary

✅ **What was fixed:**
- Changed from relative paths (`os.getcwd()`) to absolute paths (`BASE_DIR`)
- Added logging to show exact paths being checked
- Ensured directory creation with absolute paths

✅ **What to do:**
1. Pull updated code to production
2. Verify file permissions
3. Restart backend service
4. Test bulk download

✅ **How to verify it worked:**
- Check logs for "Checking for AWB label at: /home/ubuntu/backend/..."
- Bulk download should return PDF instead of 404
- No more "Label file not found" warnings

---

## Contact Points

If issues persist, check:
1. Backend logs: `tail -f /var/log/backend.log`
2. File permissions: `ls -la /home/ubuntu/backend/uploads/awb/`
3. Service status: `sudo systemctl status your-backend-service`
