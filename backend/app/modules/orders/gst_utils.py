"""
GST Calculation Utilities for SevenXT
======================================
Company registered state: Tamil Nadu (GSTIN: 33ABLCS5237N1ZU)

Rules:
  - Intra-state (buyer state == one of our registered states):
        CGST (9%) + SGST (9%) = 18% total
        Use the state-specific GSTIN on the invoice

  - Inter-state (buyer state NOT in our registered states):
        IGST (18%) only
        Use the default Tamil Nadu GSTIN

GST Rate applied to all our products: 18% total.

Usage:
    from app.modules.orders.gst_utils import compute_gst, get_seller_gstin

    breakdown = compute_gst(total_amount=1180.0, buyer_state="Tamil Nadu")
    # → {
    #       "gst_type": "intra",
    #       "subtotal": 1000.0,
    #       "cgst_rate": 9.0, "cgst_amount": 90.0,
    #       "sgst_rate": 9.0, "sgst_amount": 90.0,
    #       "igst_rate": 0.0, "igst_amount": 0.0,
    #       "total_gst": 180.0, "total": 1180.0,
    #       "seller_gstin": "33ABLCS5237N1ZU"
    #   }
"""

from typing import Dict, Any


# ---------------------------------------------------------------------------
# Registered States & their GSTINs
# ---------------------------------------------------------------------------
BASE_PAN_SUFFIX = "ABLCS5237N1ZU"
DEFAULT_GSTIN = "33ABLCS5237N1ZU"   # Tamil Nadu — default fallback

# Official 2-digit GST state codes for all Indian States & Union Territories
STATE_GST_CODES: Dict[str, str] = {
    "jammu and kashmir": "01",
    "jammu & kashmir": "01",
    "himachal pradesh": "02",
    "punjab": "03",
    "chandigarh": "04",
    "uttarakhand": "05",
    "haryana": "06",
    "delhi": "07",
    "rajasthan": "08",
    "uttar pradesh": "09",
    "bihar": "10",
    "sikkim": "11",
    "arunachal pradesh": "12",
    "nagaland": "13",
    "manipur": "14",
    "mizoram": "15",
    "tripura": "16",
    "meghalaya": "17",
    "assam": "18",
    "west bengal": "19",
    "jharkhand": "20",
    "odisha": "21",
    "orissa": "21",
    "chhattisgarh": "22",
    "madhya pradesh": "23",
    "gujarat": "24",
    "daman and diu": "26",
    "dadra and nagar haveli": "26",
    "dadra & nagar haveli": "26",
    "maharashtra": "27",
    "karnataka": "29",
    "goa": "30",
    "lakshadweep": "31",
    "kerala": "32",
    "tamil nadu": "33",
    "tamilnadu": "33",
    "puducherry": "34",
    "pondicherry": "34",
    "andaman and nicobar islands": "35",
    "andaman & nicobar": "35",
    "telangana": "36",
    "andhra pradesh": "37",
    "ladakh": "38",
}

# Key city and regional aliases mapped to state codes
CITY_STATE_CODES: Dict[str, str] = {
    "bengaluru": "29",
    "bangalore": "29",
    "silkboard": "29",
    "whitefield": "29",
    "koramangala": "29",
    "indiranagar": "29",
    "chennai": "33",
    "madras": "33",
    "coimbatore": "33",
    "madurai": "33",
    "trichy": "33",
    "salem": "33",
    "mumbai": "27",
    "bombay": "27",
    "pune": "27",
    "nagpur": "27",
    "thane": "27",
    "navi mumbai": "27",
    "hyderabad": "36",
    "secunderabad": "36",
    "kolkata": "19",
    "calcutta": "19",
    "new delhi": "07",
    "gurgaon": "06",
    "gurugram": "06",
    "faridabad": "06",
    "noida": "09",
    "greater noida": "09",
    "ghaziabad": "09",
    "lucknow": "09",
    "kanpur": "09",
    "varanasi": "09",
    "kochi": "32",
    "cochin": "32",
    "trivandrum": "32",
    "thiruvananthapuram": "32",
    "calicut": "32",
    "kozhikode": "32",
    "ahmedabad": "24",
    "surat": "24",
    "vadodara": "24",
    "rajkot": "24",
    "jaipur": "08",
    "jodhpur": "08",
    "udaipur": "08",
    "patna": "10",
    "bhopal": "23",
    "indore": "23",
    "bhubaneswar": "21",
    "cuttack": "21",
    "ranchi": "20",
    "jamshedpur": "20",
    "guwahati": "18",
    "dehradun": "05",
    "shimla": "02",
    "srinagar": "01",
    "jammu": "01",
    "visakhapatnam": "37",
    "vizag": "37",
    "vijayawada": "37",
}

# Pre-generate dictionary of registered states and their GSTINs
REGISTERED_STATES: Dict[str, str] = {
    state: f"{code}{BASE_PAN_SUFFIX}"
    for state, code in STATE_GST_CODES.items()
}

# GST split (always 18% total)
_CGST_RATE  = 9.0   # %
_SGST_RATE  = 9.0   # %
_IGST_RATE  = 18.0  # %
_TOTAL_RATE = 18.0  # %


def _normalize(state: str) -> str:
    return (state or "").strip().lower()


def find_state_code(buyer_state: str) -> str:
    """Detect the 2-digit GST state code from an address/state string."""
    s = _normalize(buyer_state)
    if not s:
        return "33"  # Default Tamil Nadu

    # 1. Check direct state names
    for state_name, code in STATE_GST_CODES.items():
        # Check whole word / substring
        if state_name in s:
            return code
        clean_state = state_name.replace(" ", "").replace("-", "")
        clean_s = s.replace(" ", "").replace("-", "")
        if clean_state in clean_s:
            return code

    # 2. Check city / regional synonyms
    for city_name, code in CITY_STATE_CODES.items():
        if city_name in s:
            return code

    # 3. Check individual tokens
    for token in s.replace(",", " ").replace(".", " ").split():
        clean_token = token.strip()
        if clean_token in CITY_STATE_CODES:
            return CITY_STATE_CODES[clean_token]
        if clean_token in STATE_GST_CODES:
            return STATE_GST_CODES[clean_token]

    return "33"


def get_seller_gstin(buyer_state: str) -> str:
    """
    Return the correct seller GSTIN based on the buyer's state.
    Uses the 2-digit state code of the local warehouse + company PAN suffix.
    """
    code = find_state_code(buyer_state)
    return f"{code}{BASE_PAN_SUFFIX}"


def is_intra_state(buyer_state: str) -> bool:
    """
    True when orders are fulfilled from the local state warehouse to customers
    in that state, resulting in intra-state taxation (CGST + SGST).
    """
    code = find_state_code(buyer_state)
    return bool(code)



def compute_gst(total_amount: float, buyer_state: str) -> Dict[str, Any]:
    """
    Compute the complete GST breakdown for an order.

    Args:
        total_amount:  The final order total (GST-inclusive amount).
        buyer_state:   The buyer's state (from the order address).

    Returns a dict with all amounts rounded to 2 decimal places:
        gst_type      : "intra" | "inter"
        subtotal      : price before GST
        cgst_rate     : 9.0 (intra) | 0.0 (inter)
        cgst_amount   : CGST rupee amount
        sgst_rate     : 9.0 (intra) | 0.0 (inter)
        sgst_amount   : SGST rupee amount
        igst_rate     : 0.0 (intra) | 18.0 (inter)
        igst_amount   : IGST rupee amount
        total_gst     : total GST collected
        total         : subtotal + total_gst  (should match total_amount)
        seller_gstin  : correct GSTIN to print on invoice
    """
    amount = float(total_amount or 0)

    # Subtotal = Total / 1.18  (reverse-calculate pre-tax price)
    subtotal = round(amount / (1 + _TOTAL_RATE / 100), 2)

    intra = is_intra_state(buyer_state)
    seller_gstin = get_seller_gstin(buyer_state)

    if intra:
        cgst_rate   = _CGST_RATE
        sgst_rate   = _SGST_RATE
        igst_rate   = 0.0
        cgst_amount = round(subtotal * cgst_rate / 100, 2)
        sgst_amount = round(subtotal * sgst_rate / 100, 2)
        igst_amount = 0.0
    else:
        cgst_rate   = 0.0
        sgst_rate   = 0.0
        igst_rate   = _IGST_RATE
        cgst_amount = 0.0
        sgst_amount = 0.0
        igst_amount = round(subtotal * igst_rate / 100, 2)

    total_gst = round(cgst_amount + sgst_amount + igst_amount, 2)
    total     = round(subtotal + total_gst, 2)

    return {
        "gst_type":     "intra" if intra else "inter",
        "subtotal":     subtotal,
        "cgst_rate":    cgst_rate,
        "cgst_amount":  cgst_amount,
        "sgst_rate":    sgst_rate,
        "sgst_amount":  sgst_amount,
        "igst_rate":    igst_rate,
        "igst_amount":  igst_amount,
        "total_gst":    total_gst,
        "total":        total,
        "seller_gstin": seller_gstin,
    }
