import requests
import json
import os
from datetime import datetime
from typing import Tuple, Optional


class DelhiveryClient:
    def __init__(self, token: str, is_production: bool = False):
        self.token = token
        self.base_url = (
            "https://track.delhivery.com"
            if is_production
            else "https://staging-express.delhivery.com"
        )

    # --------------------------------------------------
    # CREATE SHIPMENT (AWB GENERATION)
    # --------------------------------------------------
    def create_shipment(self, order_data: dict) -> dict:
        """
        Create shipment in Delhivery and generate AWB number
        Supports both forward and return shipments
        """
        url = f"{self.base_url}/api/cmu/create.json"
        print("DELHIVERY CREATE SHIPMENT URL:", url)

        # Use phone as-is from order_data (already formatted in shipment_service)
        phone = str(order_data.get("phone", ""))
        
        print(f"[DEBUG] Phone number being sent: {phone}")
        
        # Note: Reverse pickup is handled via payment_mode="Pickup" (not is_return flag)

        # Check if this is a reverse shipment
        is_reverse = order_data.get("payment_status") == "Pickup"
        
        shipment_payload = {
            "name": order_data["customer_name"],
            "add": order_data["address"],
            "pin": str(order_data["pincode"]),  # Ensure string
            "city": order_data["city"],
            "state": order_data["state"],
            "country": "India",
            "phone": str(phone),  # Ensure string
            "mobile": str(phone), # Add mobile field as well
            "email": order_data.get("email", "noreply@sevenxt.com"),  # Add email field
            "order": str(order_data["order_id"]),  # Ensure string
            "payment_mode": (
                "Pickup" if is_reverse
                else "Prepaid"  # Force Prepaid as client only uses online payment
            ),
            "products_desc": order_data.get("item_name", "Product"),
            "hsn_code": order_data.get("hsn_code", ""),
            "seller_gst_tin": order_data.get("seller_gst_tin", os.getenv("SELLER_GSTIN", "")),
            "seller_name": order_data.get("seller_name", "SevenXT Electronics"),
            "cod_amount": 0.0,  # Always 0.0 for Prepaid/Pickup
            "total_amount": float(order_data["amount"]),
            "quantity": int(order_data.get("quantity", 1)),
            # Dimensions (CM)
            "shipment_length": float(order_data["length"]),
            "shipment_width": float(order_data["breadth"]), # Renamed from breadth to width
            "shipment_height": float(order_data["height"]),
            # Weight in KG (IMPORTANT)
            "shipment_weight": float(order_data["weight"]),
            # Service Type: E (Express) or S (Surface)
            "service": order_data.get("service_type", "E"),
            
            # Return/Destination Address (for reverse pickups only)
            # These fields specify where the package should be delivered TO (warehouse)
            "return_add": "Sevenxt Electronics, Connaught Place" if is_reverse else None,
            "return_pin": "110001" if is_reverse else None,
            "return_city": "New Delhi" if is_reverse else None,
            "return_state": "Delhi" if is_reverse else None,
            "return_phone": "9363286257" if is_reverse else None,
        }
        
        # Remove None values to keep payload clean
        shipment_payload = {k: v for k, v in shipment_payload.items() if v is not None}
        
        # Delhivery API crashes with a NoneType error if GSTIN or HSN is passed as an empty string
        if shipment_payload.get("seller_gst_tin") == "":
            del shipment_payload["seller_gst_tin"]
        if shipment_payload.get("hsn_code") == "":
            del shipment_payload["hsn_code"]
        if shipment_payload.get("seller_name") == "":
            del shipment_payload["seller_name"]
        
        # For reverse pickup: payment_mode="Pickup" + customer address in main fields
        # pickup_location.name specifies the warehouse (destination)

        payload_data = {
            "shipments": [shipment_payload],
            "pickup_location": {
                # MUST MATCH EXACT NAME CREATED IN DELHIVERY
                "name": "sevenxt"
            },
        }
        
        print(f"==================================================")
        print(f"[DEBUG] FINAL PAYLOAD TO DELHIVERY:")
        print(json.dumps(payload_data, indent=2))
        print(f"==================================================")

        form_data = {
            "format": "json",
            "data": json.dumps(payload_data),
        }

        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = requests.post(url, data=form_data, headers=headers)
        print("DELHIVERY SHIPMENT RESPONSE:", response.text)
        response.raise_for_status()
        return response.json()
    
    # --------------------------------------------------
    # CREATE BULK SHIPMENTS (Multiple Orders in ONE Call)
    # --------------------------------------------------
    def create_bulk_shipment(self, orders_data: list) -> dict:
        """
        Create multiple shipments in a SINGLE Delhivery API call.
        Delhivery auto-generates a waybill for each order.
        orders_data: list of order dicts (same format as create_shipment)
        """
        url = f"{self.base_url}/api/cmu/create.json"
        print(f"[BULK SHIPMENT] Creating {len(orders_data)} shipments in one call. URL: {url}")

        shipments_list = []
        for order in orders_data:
            phone = str(order.get("phone", ""))
            is_reverse = order.get("payment_status") == "Pickup"

            shipment = {
                "name": order["customer_name"],
                "add": order["address"],
                "pin": str(order["pincode"]),
                "city": order["city"],
                "state": order["state"],
                "country": "India",
                "phone": phone,
                "mobile": phone,
                "email": order.get("email", "noreply@sevenxt.com"),
                "order": str(order["order_id"]),
                "payment_mode": "Pickup" if is_reverse else "Prepaid",
                "products_desc": order.get("item_name", "Product"),
                "hsn_code": "",
                "cod_amount": 0.0,
                "total_amount": float(order.get("amount", 0.0)),
                "quantity": int(order.get("quantity", 1)),
                "shipment_length": float(order.get("length", 10.0)),
                "shipment_width": float(order.get("breadth", 10.0)),
                "shipment_height": float(order.get("height", 10.0)),
                "shipment_weight": float(order.get("weight", 0.5)),
                "service": order.get("service_type", "E"),
            }
            # Remove None values
            shipment = {k: v for k, v in shipment.items() if v is not None}
            
            # Delhivery API crashes with a NoneType error if GSTIN or HSN is passed as an empty string
            if shipment.get("seller_gst_tin") == "":
                del shipment["seller_gst_tin"]
            if shipment.get("hsn_code") == "":
                del shipment["hsn_code"]
            if shipment.get("seller_name") == "":
                del shipment["seller_name"]
                
            shipments_list.append(shipment)

        payload_data = {
            "shipments": shipments_list,  # ← ALL orders in ONE call
            "pickup_location": {"name": "sevenxt"},
        }

        print(f"[BULK SHIPMENT] Payload has {len(shipments_list)} shipments")

        form_data = {
            "format": "json",
            "data": json.dumps(payload_data),
        }
        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = requests.post(url, data=form_data, headers=headers)
        print(f"[BULK SHIPMENT] Response: {response.text}")
        response.raise_for_status()
        return response.json()

    # --------------------------------------------------
    # PICKUP REQUEST CREATION
    # --------------------------------------------------
    def request_pickup(
        self,
        pickup_date: str,           # Format: "YYYY-MM-DD"
        pickup_time: str,           # Format: "HH:MM:SS"
        pickup_location: str = "sevenxt",   # Registered warehouse name in Delhivery
        expected_package_count: int = 1,    # Number of packages to pick up
    ) -> dict:
        """
        Call Delhivery Pickup Request Creation API.
        Must be called when shipment is packed and ready for FE pickup.

        Docs: POST /fm/request/new/
        Required: pickup_time (hh:mm:ss), pickup_date (YYYY-MM-DD),
                  pickup_location (warehouse name), expected_package_count (int)
        """
        url = f"{self.base_url}/fm/request/new/"
        print(f"[PICKUP REQUEST] Calling: {url}")
        print(f"[PICKUP REQUEST] Date={pickup_date}, Time={pickup_time}, Location={pickup_location}, Count={expected_package_count}")

        payload = {
            "pickup_time": pickup_time,
            "pickup_date": pickup_date,
            "pickup_location": pickup_location,
            "expected_package_count": expected_package_count,
        }

        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=payload, headers=headers)
        print(f"[PICKUP REQUEST] Response Status: {response.status_code}")
        print(f"[PICKUP REQUEST] Response Body: {response.text}")

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "body": response.text
            }

        try:
            return response.json()
        except Exception:
            return {"success": True, "raw": response.text}

    # --------------------------------------------------
    # CREATE WAREHOUSE / PICKUP LOCATION
    # --------------------------------------------------
    def create_warehouse(
        self,
        name: str = "sevenxt",
        address: str = "Sevenxt Electronics, Connaught Place",
        city: str = "New Delhi",
        state: str = "Delhi",
        pin: str = "110001",
        phone: str = "9363286257",
        email: str = "loguloges77@gmail.com",
        contact_person: str = "Manager",
    ) -> dict:
        url = f"{self.base_url}/api/backend/clientwarehouse/create/"

        payload = {
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "city": city,
            "state": state,
            "country": "India",
            "pin": pin,
            "return_address": address,
            "return_city": city,
            "return_state": state,
            "return_country": "India",
            "return_pin": pin,
            "contact_person": contact_person,
        }

        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json",
        }

        print(f"[DEBUG] Creating/Updating Warehouse with payload: {json.dumps(payload, indent=2)}")

        response = requests.post(url, json=payload, headers=headers)
        print("WAREHOUSE RESPONSE:", response.text)
        response.raise_for_status()
        return response.json()

    # --------------------------------------------------
    # FETCH WAREHOUSE DETAILS (WITH CACHING)
    # --------------------------------------------------
    def get_warehouse_details(self, warehouse_name: str = "sevenxt") -> dict:
        """
        Fetch warehouse/pickup location details from Delhivery
        Returns warehouse address, phone, pincode, etc.
        
        This is cached to avoid repeated API calls.
        Falls back to default values if API fails.
        """
        url = f"{self.base_url}/api/backend/clientwarehouse/all/"
        
        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json",
        }
        
        try:
            print(f"[WAREHOUSE] Fetching warehouse details for: {warehouse_name}")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                warehouses = data.get("data", [])
                
                # Find the warehouse by name
                for warehouse in warehouses:
                    if warehouse.get("name") == warehouse_name:
                        print(f"[WAREHOUSE] Found warehouse: {warehouse.get('address')}")
                        return {
                            "name": warehouse.get("name", warehouse_name),
                            "address": warehouse.get("address", ""),
                            "city": warehouse.get("city", "Chennai"),
                            "state": warehouse.get("state", "Tamil Nadu"),
                            "pincode": warehouse.get("pin", "600014"),
                            "phone": warehouse.get("phone", "9363286257"),
                            "email": warehouse.get("email", "loguloges77@gmail.com"),
                        }
                
                print(f"[WAREHOUSE] WARNING: Warehouse '{warehouse_name}' not found in API response")
            else:
                print(f"[WAREHOUSE] WARNING: API returned status {response.status_code}")
                
        except Exception as e:
            print(f"[WAREHOUSE] WARNING: Error fetching warehouse: {e}")
        
        # Fallback to default values if API fails or warehouse not found
        print(f"[WAREHOUSE] Using default warehouse values")
        return {
            "name": warehouse_name,
            "address": "Sevenxt Electronics, Connaught Place",
            "city": "New Delhi",
            "state": "Delhi",
            "pincode": "110001",
            "phone": "9363286257",
            "email": "loguloges77@gmail.com",
        }

    # --------------------------------------------------
    # FETCH AWB LABEL (PDF)
    # --------------------------------------------------
    def fetch_awb_label(self, waybill: str) -> Tuple[Optional[bytes], Optional[dict]]:
        """
        Fetch AWB label PDF using waybill number
        """
        # Use api.delhivery.com for labels specifically, as track.delhivery.com can be flaky for packing_slip
        label_base_url = "https://api.delhivery.com" if "track.delhivery.com" in self.base_url else self.base_url
        url = f"{label_base_url}/api/p/packing_slip"
        
        params = {
            "wbns": waybill,
            "pdf": "true",
            "ss": "100x150",  # Request 100mm x 150mm (4x6 inch) size
        }

        headers = {
            "Authorization": f"Token {self.token}",
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code != 200:
                print(f"LABEL FETCH FAILED: {response.text}")
                return None, {"error": f"Status {response.status_code}", "body": response.text}

            content_type = response.headers.get("content-type", "")

            if "application/pdf" in content_type:
                return response.content, None
            
            try:
                data = response.json()
                # Check if it contains packages with PDF link/content
                if isinstance(data, dict) and 'packages' in data and len(data['packages']) > 0:
                    pkg = data['packages'][0]
                    pdf_link = pkg.get('pdf_download_link')
                    if pdf_link:
                        if pdf_link.startswith('http'):
                            # Download it
                            print(f"Downloading label from {pdf_link}")
                            pdf_resp = requests.get(pdf_link)
                            if pdf_resp.status_code == 200:
                                return pdf_resp.content, None
                        elif pdf_link.startswith('%PDF'):
                             # It's raw content
                             return pdf_link.encode('utf-8'), None
                        else:
                             # Maybe base64?
                             pass
                
                return None, data
            except:
                return None, {"error": "Unknown response format", "body": response.text}
                
        except Exception as e:
            print(f"EXCEPTION IN FETCH_LABEL: {e}")
            return None, {"error": str(e)}


    # --------------------------------------------------
    # PICKUP REQUEST (unified method)
    # --------------------------------------------------
    def pickup_request(self, pickup_data: dict) -> dict:
        """
        Schedule a pickup request.
        Accepts a dict with: pickup_time, pickup_date, pickup_location, expected_package_count
        Also works as request_pickup() — both signatures are supported.
        """
        url = f"{self.base_url}/fm/request/new/"
        print(f"[PICKUP REQUEST] Calling: {url}")

        payload = {
            "pickup_time": pickup_data.get("pickup_time"),
            "pickup_date": pickup_data.get("pickup_date"),
            "pickup_location": pickup_data.get("pickup_location", "sevenxt"),
            "expected_package_count": pickup_data.get("expected_package_count", 1),
        }

        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json",
        }

        print(f"[PICKUP REQUEST] Payload: {payload}")
        response = requests.post(url, json=payload, headers=headers)
        print(f"[PICKUP REQUEST] Response ({response.status_code}): {response.text}")
        
        if response.status_code not in [200, 201]:
             try:
                 err = response.json()
                 raise Exception(f"Delhivery Pickup API Error: {err}")
             except ValueError:
                 raise Exception(f"Delhivery Pickup API Error: {response.text}")
                 
        return response.json()

    # --------------------------------------------------
    # CANCEL SHIPMENT
    # --------------------------------------------------
    def cancel_shipment(self, waybill: str) -> dict:
        """
        Cancel a shipment using the Edit API.
        Only works for statuses: Manifested, In Transit, Pending, Open, Scheduled.
        Docs: POST /api/p/edit with cancellation=true
        """
        url = f"{self.base_url}/api/p/edit"
        print(f"[CANCEL] Cancelling shipment AWB: {waybill}")

        payload = {
            "waybill": waybill,
            "cancellation": "true",
        }

        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=payload, headers=headers)
        print(f"[CANCEL] Response ({response.status_code}): {response.text}")
        
        try:
            return response.json()
        except Exception:
            return {"status_code": response.status_code, "body": response.text}

    # --------------------------------------------------
    # UPDATE SHIPMENT (Weight/Dimensions/Address)
    # --------------------------------------------------
    def update_shipment(self, waybill: str, updates: dict) -> dict:
        """
        Update shipment details via the Edit API.
        Only works before physical pickup (Manifested, Pending, Scheduled).
        
        Supported update fields:
          gm (weight in grams), shipment_length, shipment_width, shipment_height,
          name, add, phone, cod (COD amount), pt (payment type)
        """
        url = f"{self.base_url}/api/p/edit"
        print(f"[UPDATE] Updating shipment AWB: {waybill} with: {updates}")

        payload = {"waybill": waybill, **updates}

        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=payload, headers=headers)
        print(f"[UPDATE] Response ({response.status_code}): {response.text}")

        try:
            return response.json()
        except Exception:
            return {"status_code": response.status_code, "body": response.text}

    # --------------------------------------------------
    # TRACK SHIPMENT (Polling Fallback)
    # --------------------------------------------------
    def track_shipment(self, waybill: str) -> dict:
        """
        Track shipment status by AWB number.
        Use as fallback when webhooks fail or for on-demand status check.
        Supports up to 50 comma-separated waybills.
        Docs: GET /api/v1/packages/json/?waybill={waybill}
        """
        url = f"{self.base_url}/api/v1/packages/json/"
        params = {
            "waybill": waybill,
            "token": self.token,
        }

        print(f"[TRACK] Tracking AWB: {waybill}")
        response = requests.get(url, params=params, timeout=10)
        print(f"[TRACK] Response ({response.status_code})")

        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}", "body": response.text}

        try:
            return response.json()
        except Exception:
            return {"error": "Invalid JSON response", "body": response.text}

    # --------------------------------------------------
    # PINCODE SERVICEABILITY CHECK
    # --------------------------------------------------
    def check_pincode_serviceability(self, pincode: str) -> dict:
        """
        Check if a pincode is serviceable by Delhivery.
        Returns serviceability status and details.
        Docs: GET /c/api/pin-codes/json/?filter_codes={pincode}
        """
        url = f"{self.base_url}/c/api/pin-codes/json/"
        params = {"filter_codes": pincode}
        headers = {"Authorization": f"Token {self.token}"}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=5)
            
            if response.status_code != 200:
                return {"serviceable": False, "reason": f"API error: HTTP {response.status_code}"}

            data = response.json()
            delivery_codes = data.get("delivery_codes", [])

            if not delivery_codes:
                return {"serviceable": False, "reason": "NSZ (Non-serviceable pincode)"}

            pincode_info = delivery_codes[0].get("postal_code", {})
            remark = pincode_info.get("remarks", "")

            if remark.lower() == "embargo":
                return {"serviceable": False, "reason": "Temporarily unavailable (Embargo)"}

            return {
                "serviceable": True,
                "reason": "Serviceable",
                "data": pincode_info,
            }
        except Exception as e:
            print(f"[PINCODE] Error checking serviceability: {e}")
            return {"serviceable": False, "reason": f"Error: {str(e)}"}


# --------------------------------------------------
# INITIALIZATION
# --------------------------------------------------
DELHIVERY_API_TOKEN = os.getenv("DELHIVERY_API_TOKEN", "")
IS_PRODUCTION = os.getenv("DELHIVERY_PRODUCTION", "false").lower() == "true"

if not DELHIVERY_API_TOKEN:
    print("[WARNING] DELHIVERY_API_TOKEN env var is not set! Delhivery API calls will fail.")

delhivery_client = DelhiveryClient(
    token=DELHIVERY_API_TOKEN,
    is_production=IS_PRODUCTION,
)
