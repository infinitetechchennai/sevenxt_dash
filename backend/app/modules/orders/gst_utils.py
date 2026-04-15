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
# Add more states here when/if the company gets registered in additional states.
# Key must be the EXACT state name as received from the mobile app / order data
# (comparison is case-insensitive – see _normalize below).

REGISTERED_STATES: Dict[str, str] = {
    "tamil nadu": "33ABLCS5237N1ZU",
    # "karnataka": "29ABLCS5237N1ZU",  # Example — fill in when registered
}

DEFAULT_GSTIN = "33ABLCS5237N1ZU"   # Tamil Nadu — used for inter-state

# GST split (always 18% total)
_CGST_RATE  = 9.0   # % — was wrongly 8% before, now corrected to 9%
_SGST_RATE  = 9.0   # %
_IGST_RATE  = 18.0  # %
_TOTAL_RATE = 18.0  # %


def _normalize(state: str) -> str:
    return (state or "").strip().lower()


def get_seller_gstin(buyer_state: str) -> str:
    """Return the correct seller GSTIN based on the buyer's state."""
    s = _normalize(buyer_state)
    # Be resilient to variants like "Tamilnadu", "Tamil Nadu - India", etc.
    for key, gstin in REGISTERED_STATES.items():
        k = _normalize(key)
        if not k:
            continue
        if s == k or k in s or s.replace(" ", "") == k.replace(" ", ""):
            return gstin
    return DEFAULT_GSTIN


def is_intra_state(buyer_state: str) -> bool:
    """True when buyer's state is one of our registered states."""
    s = _normalize(buyer_state)
    for key in REGISTERED_STATES.keys():
        k = _normalize(key)
        if not k:
            continue
        if s == k or k in s or s.replace(" ", "") == k.replace(" ", ""):
            return True
    return False


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
