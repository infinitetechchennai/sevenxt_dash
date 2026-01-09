# 📡 How Delhivery Sends JSON - Complete Guide

**Date:** 2026-01-09 17:57 IST  
**Source:** Official Delhivery B2C API Documentation + SPOC Webhook Requirement v3.0

---

## 🔄 THE COMPLETE FLOW

### **When Delivery Boy Scans the AWB Barcode:**

```
1. Delivery boy scans AWB barcode with handheld device
   ↓
2. Delhivery system records the scan
   ↓
3. Delhivery server prepares JSON payload
   ↓
4. Delhivery sends HTTP POST request to your webhook URL
   ↓
5. Your server receives and processes the JSON
   ↓
6. Your server responds with {"status": "success"}
```

---

## 📦 JSON FORMATS DELHIVERY SENDS

According to the documentation, Delhivery sends **TWO different JSON formats**:

---

## **FORMAT 1: Custom/Simple Payload** (Recommended by Delhivery)

### **When Sent:**
- For simple status updates
- When you configure "custom payload" in Delhivery dashboard

### **JSON Structure:**

```json
{
  "waybill": "1234567890",
  "status": "Delivered"
}
```

### **Fields:**
- `waybill` (string): The AWB number
- `status` (string): Current delivery status

### **Example Scenarios:**

#### **Scenario 1: Pickup from Customer**
```json
{
  "waybill": "ABC123456789",
  "status": "Picked Up"
}
```

#### **Scenario 2: In Transit**
```json
{
  "waybill": "ABC123456789",
  "status": "In Transit"
}
```

#### **Scenario 3: Delivered to Warehouse**
```json
{
  "waybill": "ABC123456789",
  "status": "Delivered"
}
```

---

## **FORMAT 2: Detailed Payload with Scans Array** (Default)

### **When Sent:**
- Default format from Delhivery
- Contains full scan history
- Includes timestamps and locations

### **JSON Structure:**

```json
{
  "waybill": "1234567890",
  "scans": [
    {
      "ScanDetail": {
        "Scan": "Picked Up",
        "ScanType": "UD",
        "ScanDateTime": "2022-09-16 08:30:00",
        "ScannedLocation": "Mumbai Hub",
        "Instructions": "Package picked up from customer",
        "Remarks": ""
      }
    },
    {
      "ScanDetail": {
        "Scan": "In Transit",
        "ScanType": "IT",
        "ScanDateTime": "2022-09-16 12:45:00",
        "ScannedLocation": "Pune Hub",
        "Instructions": "In transit to destination",
        "Remarks": ""
      }
    },
    {
      "ScanDetail": {
        "Scan": "Delivered",
        "ScanType": "DL",
        "ScanDateTime": "2022-09-16 18:00:00",
        "ScannedLocation": "Delhi Warehouse",
        "Instructions": "Delivered to warehouse",
        "Remarks": "Received by: John Doe"
      }
    }
  ]
}
```

### **Fields in Each Scan:**
- `Scan` (string): Human-readable status (e.g., "Picked Up", "Delivered")
- `ScanType` (string): Status code (e.g., "PU", "IT", "DL")
- `ScanDateTime` (string): When the scan happened
- `ScannedLocation` (string): Where the scan happened
- `Instructions` (string): Additional instructions
- `Remarks` (string): Any remarks from delivery boy

---

## 🎯 REAL-WORLD EXAMPLE: Complete Journey

### **Your Refund Scenario:**

**Customer:** John Doe, Mumbai  
**Warehouse:** SevenXT Warehouse, Delhi  
**AWB:** ABC123456789

---

### **8:00 AM - Delivery Boy Goes to Customer's House**

**What Happens:**
1. Delivery boy arrives at customer's address
2. Scans AWB barcode: `ABC123456789`
3. Selects "Picked Up" on handheld device
4. Delhivery system records the scan

**JSON Sent to Your Webhook:**

#### **Option A: Simple Format**
```json
{
  "waybill": "ABC123456789",
  "status": "Picked Up"
}
```

#### **Option B: Detailed Format**
```json
{
  "waybill": "ABC123456789",
  "scans": [
    {
      "ScanDetail": {
        "Scan": "Picked Up",
        "ScanType": "PU",
        "ScanDateTime": "2026-01-09 08:00:00",
        "ScannedLocation": "Customer Address, Mumbai, 400001",
        "Instructions": "Reverse pickup for refund",
        "Remarks": "Package condition: Good"
      }
    }
  ]
}
```

**HTTP Request:**
```http
POST https://your-domain.com/webhooks/delhivery/return
Content-Type: application/json

{
  "waybill": "ABC123456789",
  "scans": [...]
}
```

**Your Server Should Respond:**
```json
{
  "status": "success"
}
```

---

### **12:00 PM - Package Reaches Transit Hub**

**What Happens:**
1. Package arrives at Pune hub
2. Hub staff scans AWB
3. Selects "In Transit"

**JSON Sent:**

```json
{
  "waybill": "ABC123456789",
  "scans": [
    {
      "ScanDetail": {
        "Scan": "Picked Up",
        "ScanDateTime": "2026-01-09 08:00:00",
        "ScannedLocation": "Mumbai"
      }
    },
    {
      "ScanDetail": {
        "Scan": "In Transit",
        "ScanType": "IT",
        "ScanDateTime": "2026-01-09 12:00:00",
        "ScannedLocation": "Pune Hub",
        "Instructions": "In transit to Delhi"
      }
    }
  ]
}
```

**Notice:** Scans array now has **2 items** (full history)

---

### **6:00 PM - Package Delivered to Your Warehouse**

**What Happens:**
1. Package arrives at your warehouse in Delhi
2. Delivery boy scans AWB
3. Your warehouse staff signs
4. Delivery boy marks "Delivered"

**JSON Sent:**

```json
{
  "waybill": "ABC123456789",
  "scans": [
    {
      "ScanDetail": {
        "Scan": "Picked Up",
        "ScanDateTime": "2026-01-09 08:00:00",
        "ScannedLocation": "Mumbai"
      }
    },
    {
      "ScanDetail": {
        "Scan": "In Transit",
        "ScanDateTime": "2026-01-09 12:00:00",
        "ScannedLocation": "Pune Hub"
      }
    },
    {
      "ScanDetail": {
        "Scan": "Delivered",
        "ScanType": "DL",
        "ScanDateTime": "2026-01-09 18:00:00",
        "ScannedLocation": "SevenXT Warehouse, Delhi, 110001",
        "Instructions": "Delivered to warehouse",
        "Remarks": "Received by: Warehouse Manager, Signature: Yes"
      }
    }
  ]
}
```

**Notice:** Scans array now has **3 items** (complete journey)

---

## 📊 ALL POSSIBLE STATUS CODES

According to Delhivery documentation:

| Scan Type | Scan Value | Meaning |
|-----------|------------|---------|
| `PU` | "Picked Up" | Package picked up from customer |
| `IT` | "In Transit" | Package in transit between hubs |
| `OD` | "Out For Delivery" | Out for delivery to destination |
| `DL` | "Delivered" | Successfully delivered |
| `UD` | "Undelivered" | Delivery attempt failed |
| `RT` | "Return" | Package being returned |
| `RTO` | "Return to Origin" | Returning to sender |
| `CN` | "Cancelled" | Shipment cancelled |
| `EX` | "Exception" | Exception occurred |

---

## 🔍 HOW TO IDENTIFY WHICH FORMAT

### **Method 1: Check for 'status' Field**

```python
if 'status' in payload:
    # Simple format
    status = payload['status']
else:
    # Detailed format with scans
    status = payload['scans'][-1]['ScanDetail']['Scan']
```

### **Method 2: Check for 'scans' Field**

```python
if 'scans' in payload:
    # Detailed format
    latest_scan = payload['scans'][-1]
    status = latest_scan['ScanDetail']['Scan']
else:
    # Simple format
    status = payload['status']
```

---

## 💻 COMPLETE WEBHOOK CODE TO HANDLE BOTH FORMATS

```python
@router.post("/webhooks/delhivery/return")
async def delhivery_return_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Delhivery webhook - supports BOTH formats
    """
    try:
        payload = await request.json()
        logger.info(f"[WEBHOOK] Received: {payload}")
        
        # Extract waybill (AWB number)
        waybill = payload.get('waybill') or payload.get('awb')
        
        # Extract status - Try multiple sources
        status = None
        scan_datetime = None
        scanned_location = None
        
        # FORMAT 1: Simple payload
        if 'status' in payload:
            status = payload.get('status')
            logger.info(f"[WEBHOOK] Simple format - Status: {status}")
        
        # FORMAT 2: Detailed payload with scans array
        elif 'scans' in payload:
            scans = payload.get('scans', [])
            if scans and len(scans) > 0:
                # Get the LATEST scan (last item)
                latest_scan = scans[-1]
                scan_detail = latest_scan.get('ScanDetail', {})
                
                # Extract all fields
                status = (scan_detail.get('Scan') or 
                         scan_detail.get('Status') or 
                         scan_detail.get('ScanType'))
                scan_datetime = scan_detail.get('ScanDateTime')
                scanned_location = scan_detail.get('ScannedLocation')
                
                logger.info(f"[WEBHOOK] Detailed format - Status: {status}")
                logger.info(f"[WEBHOOK] Scan Time: {scan_datetime}")
                logger.info(f"[WEBHOOK] Location: {scanned_location}")
        
        # Validate
        if not waybill or not status:
            logger.error("[WEBHOOK] Missing waybill or status")
            return {"status": "error", "message": "Missing required fields"}
        
        # Find refund by AWB
        refund = db.query(Refund).filter(
            Refund.return_awb_number == waybill
        ).first()
        
        if not refund:
            logger.warning(f"[WEBHOOK] No refund found for AWB: {waybill}")
            return {"status": "not_found"}
        
        # Update status
        old_status = refund.return_delivery_status
        refund.return_delivery_status = status
        
        logger.info(f"[WEBHOOK] Updated refund {refund.id}: {old_status} → {status}")
        
        # Handle specific statuses
        if status.lower() in ['delivered', 'dlvd', 'dl']:
            logger.info(f"[WEBHOOK] ✅ Package delivered to warehouse!")
            # TODO: Notify admin to verify product
        
        # Commit to database
        db.commit()
        
        # Return success (< 200ms as per documentation)
        return {"status": "success"}
        
    except Exception as e:
        logger.exception(f"[WEBHOOK] Error: {e}")
        db.rollback()
        return {"status": "error", "message": str(e)}
```

---

## 🎯 SUMMARY

### **How Delhivery Sends JSON:**

1. **When:** Delivery boy scans AWB barcode
2. **Method:** HTTP POST request
3. **URL:** Your webhook endpoint
4. **Content-Type:** application/json

### **Two Formats:**

**Simple:**
```json
{"waybill": "ABC", "status": "Delivered"}
```

**Detailed:**
```json
{
  "waybill": "ABC",
  "scans": [{
    "ScanDetail": {
      "Scan": "Delivered",
      "ScanDateTime": "2026-01-09 18:00:00",
      "ScannedLocation": "Warehouse"
    }
  }]
}
```

### **Your Code Must:**
1. ✅ Accept POST requests
2. ✅ Parse JSON payload
3. ✅ Check BOTH `status` and `scans` fields
4. ✅ Extract latest scan from scans array
5. ✅ Update database
6. ✅ Respond with `{"status": "success"}` within 200ms

---

**Report Generated:** 2026-01-09 17:57 IST  
**Source:** Official Delhivery Documentation  
**Format Coverage:** Both Simple and Detailed  
**Real-World Examples:** Included
