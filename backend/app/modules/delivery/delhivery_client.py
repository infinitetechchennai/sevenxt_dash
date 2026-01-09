import requests
import json
from datetime import datetime
from typing import Tuple, Optional


class DelhiveryClient:
    def __init__(self, token: str, is_production: bool = False):
        self.token = token
        self.base_url = (
            "https://api.delhivery.com"
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
                "Pickup" if order_data.get("payment_status") == "Pickup"
                else "Prepaid" if order_data.get("payment_status") in ["Paid", "Prepaid"]
                else "COD"
            ),
            "products_desc": order_data.get("item_name", "Product"),
            "hsn_code": "",
            "cod_amount": (
                0.0
                if order_data.get("payment_status") in ["Paid", "Prepaid"]
                else float(order_data["amount"])
            ),
            "order_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_amount": float(order_data["amount"]),
            "quantity": int(order_data.get("quantity", 1)),
            # Dimensions (CM)
            "shipment_length": float(order_data["length"]),
            "shipment_breadth": float(order_data["breadth"]),
            "shipment_height": float(order_data["height"]),
            # Weight in KG (IMPORTANT)
            "shipment_weight": float(order_data["weight"]),
            # Service Type: E (Express) or S (Surface)
            "service": order_data.get("service_type", "E"),
        }
        
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
    # CREATE WAREHOUSE / PICKUP LOCATION
    # --------------------------------------------------
    def create_warehouse(
        self,
        name: str = "sevenxt",
        address: str = "Sevenxt Electroic pvt ltd ",
        city: str = "chennai",
        state: str = "Tamil nadu",
        pin: str = "600014",
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
            "address": "Sevenxt Electronic pvt ltd, Chennai",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "pincode": "600014",
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
        url = f"{self.base_url}/api/p/packing_slip"
        params = {
            "wbns": waybill,
            "pdf": "true",
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
    # PICKUP REQUEST
    # --------------------------------------------------
    def pickup_request(self, pickup_data: dict) -> dict:
        """
        Schedule a pickup request
        """
        url = f"{self.base_url}/fm/request/new/"
        print("DELHIVERY PICKUP REQUEST URL:", url)

        payload = {
            "pickup_time": pickup_data.get("pickup_time"),
            "pickup_date": pickup_data.get("pickup_date"),
            "pickup_location": pickup_data.get("pickup_location"),
            "expected_package_count": pickup_data.get("expected_package_count", 1),
        }

        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=payload, headers=headers)
        print("PICKUP REQUEST RESPONSE:", response.text)
        
        # Delhivery returns 201 for success usually, but we check for errors
        if response.status_code not in [200, 201]:
             # Try to parse error
             try:
                 err = response.json()
                 raise Exception(f"Delhivery API Error: {err}")
             except:
                 raise Exception(f"Delhivery API Error: {response.text}")
                 
        return response.json()


# --------------------------------------------------
# INITIALIZATION (SANDBOX)
# --------------------------------------------------

DELHIVERY_TEST_TOKEN = "cb5e84d71ecff61c73abc80b20b326dec8302d8c"

delhivery_client = DelhiveryClient(
    token=DELHIVERY_TEST_TOKEN,
    is_production=False,
)
