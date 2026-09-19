"""
SevenXt Tax Invoice / Bill of Supply / Cash Memo Generator
==========================================================
Generates an Amazon-style A4 Tax Invoice with SevenXt branding.
All fields (addresses, state codes, GSTIN, PAN, items, tax breakdown,
amounts, amount in words, and dates) are 100% dynamic.
"""

import os
import json
import logging
from datetime import datetime
from typing import Union, Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.units import mm

from app.modules.orders.order_id_generator import derive_invoice_number
from app.modules.orders.gst_utils import compute_gst, find_state_code

logger = logging.getLogger(__name__)

# Map 2-digit GST state codes to official State Names
CODE_TO_STATE_NAME = {
    "01": "JAMMU AND KASHMIR",
    "02": "HIMACHAL PRADESH",
    "03": "PUNJAB",
    "04": "CHANDIGARH",
    "05": "UTTARAKHAND",
    "06": "HARYANA",
    "07": "DELHI",
    "08": "RAJASTHAN",
    "09": "UTTAR PRADESH",
    "10": "BIHAR",
    "11": "SIKKIM",
    "12": "ARUNACHAL PRADESH",
    "13": "NAGALAND",
    "14": "MANIPUR",
    "15": "MIZORAM",
    "16": "TRIPURA",
    "17": "MEGHALAYA",
    "18": "ASSAM",
    "19": "WEST BENGAL",
    "20": "JHARKHAND",
    "21": "ODISHA",
    "22": "CHHATTISGARH",
    "23": "MADHYA PRADESH",
    "24": "GUJARAT",
    "26": "DADRA AND NAGAR HAVELI AND DAMAN AND DIU",
    "27": "MAHARASHTRA",
    "29": "KARNATAKA",
    "30": "GOA",
    "31": "LAKSHADWEEP",
    "32": "KERALA",
    "33": "TAMIL NADU",
    "34": "PUDUCHERRY",
    "35": "ANDAMAN AND NICOBAR ISLANDS",
    "36": "TELANGANA",
    "37": "ANDHRA PRADESH",
    "38": "LADAKH",
}


def number_to_words(n: float) -> str:
    """Converts a number to English words in Indian currency denomination."""
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def _convert_below_thousand(num: int) -> str:
        parts = []
        if num >= 100:
            parts.append(ones[num // 100] + " Hundred")
            num %= 100
        if num >= 20:
            t = tens[num // 10]
            o = ones[num % 10]
            parts.append(f"{t}-{o.lower()}" if o else t)
        elif num > 0:
            parts.append(ones[num])
        return " ".join(parts)

    int_part = int(round(n))
    if int_part == 0:
        return "Zero only"

    crore = int_part // 10000000
    int_part %= 10000000
    lakh = int_part // 100000
    int_part %= 100000
    thousand = int_part // 1000
    int_part %= 1000
    remainder = int_part

    parts = []
    if crore > 0:
        parts.append(_convert_below_thousand(crore) + " Crore")
    if lakh > 0:
        parts.append(_convert_below_thousand(lakh) + " Lakh")
    if thousand > 0:
        parts.append(_convert_below_thousand(thousand) + " Thousand")
    if remainder > 0:
        parts.append(_convert_below_thousand(remainder))

    words = " ".join(parts).strip()
    return f"{words} only"


def _normalize_order_data(order: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    """Extract standard dict keys whether input is SQLAlchemy model or dictionary."""
    if isinstance(order, dict):
        d = dict(order)
    else:
        d = {
            "id": getattr(order, "id", None),
            "order_id": getattr(order, "order_id", None),
            "razorpay_order_id": getattr(order, "razorpay_order_id", None),
            "customer": getattr(order, "customer_name", None),
            "customer_name": getattr(order, "customer_name", None),
            "address": getattr(order, "address", None),
            "city": getattr(order, "city", None),
            "state": getattr(order, "state", None),
            "pincode": getattr(order, "pincode", None),
            "phone": getattr(order, "phone", None),
            "email": getattr(order, "email", None),
            "amount": getattr(order, "amount", None),
            "products": getattr(order, "products", None),
            "hsn": getattr(order, "hsn", None),
            "created_at": getattr(order, "created_at", None),
        }

    try:
        d["amount"] = float(d.get("amount") or 0.0)
    except Exception:
        d["amount"] = 0.0

    products = d.get("products")
    if isinstance(products, str):
        try:
            d["products"] = json.loads(products)
        except Exception:
            d["products"] = []
    elif not isinstance(products, list):
        d["products"] = []

    return d


def generate_invoice_pdf(order: Union[Dict[str, Any], Any], output_dir: str, prefix: str = "invoice") -> str:
    """
    Generates a high-quality Amazon-style A4 Tax Invoice / Bill of Supply PDF.
    """
    os.makedirs(output_dir, exist_ok=True)
    order_data = _normalize_order_data(order)

    oid = order_data.get("order_id") or str(order_data.get("id", "ORDER"))
    filename = f"{prefix}_{oid}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm
    )

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle('Norm', fontName='Helvetica', fontSize=8, leading=11)
    style_bold = ParagraphStyle('Bold', fontName='Helvetica-Bold', fontSize=8, leading=11)
    style_title_right = ParagraphStyle('TitleRight', fontName='Helvetica-Bold', fontSize=9, leading=12, alignment=TA_RIGHT)
    style_tbl_hdr = ParagraphStyle('TblHdr', fontName='Helvetica-Bold', fontSize=7, leading=9, alignment=TA_CENTER)
    style_cell_left = ParagraphStyle('CellLeft', fontName='Helvetica', fontSize=7, leading=9, alignment=TA_LEFT)
    style_cell_center = ParagraphStyle('CellCenter', fontName='Helvetica', fontSize=7, leading=9, alignment=TA_CENTER)
    style_cell_right = ParagraphStyle('CellRight', fontName='Helvetica', fontSize=7, leading=9, alignment=TA_RIGHT)
    style_cell_bold_right = ParagraphStyle('CellBoldRight', fontName='Helvetica-Bold', fontSize=8, leading=10, alignment=TA_RIGHT)

    elements = []

    # 1. Header (SevenXt Logo/Branding on Left, Tax Invoice Title on Right)
    brand_html = '<font size=22 color="#111827"><b>sevenxt</b></font><font size=16 color="#e11d48"><b>.in</b></font>'
    header_right = (
        '<b>Tax Invoice/Bill of Supply/Cash Memo</b><br/>'
        '<font color="#374151">(Triplicate for Supplier)</font>'
    )
    t_header = Table(
        [[Paragraph(brand_html, style_normal), Paragraph(header_right, style_title_right)]],
        colWidths=[100 * mm, 90 * mm]
    )
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_header)
    elements.append(Spacer(1, 4 * mm))

    # Location & GST Resolution
    buyer_state = str(order_data.get("state") or "").strip()
    buyer_city = str(order_data.get("city") or "").strip()
    buyer_pin = str(order_data.get("pincode") or "").strip()
    buyer_addr = str(order_data.get("address") or "").strip()
    buyer_name = str(order_data.get("customer") or order_data.get("customer_name") or "Customer").strip()
    buyer_phone = str(order_data.get("phone") or "").strip()

    loc_combined = f"{buyer_state} {buyer_city} {buyer_addr}".strip()
    state_code = find_state_code(loc_combined)
    state_name = CODE_TO_STATE_NAME.get(state_code, buyer_state.upper() if buyer_state else "TAMIL NADU")

    final_amount = float(order_data.get("amount") or 0.0)
    gst_info = compute_gst(total_amount=final_amount, buyer_state=loc_combined)
    seller_gstin = gst_info.get("seller_gstin") or f"{state_code}ABLCS5237N1ZU"
    seller_pan = seller_gstin[2:12] if len(seller_gstin) >= 12 else "ABLCS5237N"
    is_intra = (gst_info.get("gst_type") == "intra")

    # 2. Addresses Block (Sold By on Left, Billing/Shipping on Right)
    sold_by_html = (
        '<b>Sold By :</b><br/>'
        '<b>Sevenxt Electronic Pvt Ltd.</b><br/>'
        'No.181/1 - Second Floor, Swamy Naicken Street,<br/>'
        'Chintadripet, Chennai, TAMIL NADU, 600002<br/>'
        'IN<br/><br/>'
        f'<b>PAN No:</b> {seller_pan}<br/>'
        f'<b>GST Registration No:</b> {seller_gstin}'
    )

    cust_addr_lines = buyer_addr
    if buyer_city or buyer_pin or buyer_state:
        parts = [p for p in [buyer_city, buyer_state] if p]
        city_st = ", ".join(parts)
        if buyer_pin:
            city_st += f" - {buyer_pin}"
        if city_st:
            cust_addr_lines += f"<br/>{city_st}"
    cust_addr_lines += "<br/>IN"
    if buyer_phone:
        cust_addr_lines += f"<br/>Ph: {buyer_phone}"

    right_addr_html = (
        '<b>Billing Address :</b><br/>'
        f'{buyer_name}<br/>'
        f'{cust_addr_lines}<br/>'
        f'<b>State/UT Code:</b> {state_code}<br/><br/>'
        '<b>Shipping Address :</b><br/>'
        f'{buyer_name}<br/>'
        f'{cust_addr_lines}<br/>'
        f'<b>State/UT Code:</b> {state_code}<br/>'
        f'<b>Place of supply:</b> {state_name}<br/>'
        f'<b>Place of delivery:</b> {state_name}'
    )

    t_addresses = Table(
        [[Paragraph(sold_by_html, style_normal), Paragraph(right_addr_html, style_normal)]],
        colWidths=[95 * mm, 95 * mm]
    )
    t_addresses.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_addresses)
    elements.append(Spacer(1, 4 * mm))

    # 3. Order & Invoice Meta Block
    created_at = order_data.get("created_at")
    if isinstance(created_at, datetime):
        order_date_str = created_at.strftime("%d.%m.%Y")
    elif order_data.get("date"):
        order_date_str = str(order_data.get("date"))
    else:
        order_date_str = datetime.now().strftime("%d.%m.%Y")

    display_order_id = order_data.get("razorpay_order_id") or oid
    inv_num = derive_invoice_number(oid)
    inv_details = f"{state_code}-{str(oid)[-10:].replace('-', '')}"

    left_meta_html = (
        f'<b>Order Number:</b> {display_order_id}<br/>'
        f'<b>Order Date:</b> {order_date_str}'
    )
    right_meta_html = (
        f'<b>Invoice Number :</b> {inv_num}<br/>'
        f'<b>Invoice Details :</b> {inv_details}<br/>'
        f'<b>Invoice Date :</b> {order_date_str}'
    )

    t_meta = Table(
        [[Paragraph(left_meta_html, style_normal), Paragraph(right_meta_html, style_normal)]],
        colWidths=[95 * mm, 95 * mm]
    )
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 3 * mm))

    # 4. Items Table
    col_widths = [8 * mm, 68 * mm, 18 * mm, 10 * mm, 18 * mm, 14 * mm, 14 * mm, 18 * mm, 22 * mm]
    table_data = [
        [
            Paragraph("<b>Sl.<br/>No</b>", style_tbl_hdr),
            Paragraph("<b>Description</b>", style_tbl_hdr),
            Paragraph("<b>Unit<br/>Price</b>", style_tbl_hdr),
            Paragraph("<b>Qty</b>", style_tbl_hdr),
            Paragraph("<b>Net<br/>Amount</b>", style_tbl_hdr),
            Paragraph("<b>Tax<br/>Rate</b>", style_tbl_hdr),
            Paragraph("<b>Tax<br/>Type</b>", style_tbl_hdr),
            Paragraph("<b>Tax<br/>Amount</b>", style_tbl_hdr),
            Paragraph("<b>Total<br/>Amount</b>", style_tbl_hdr),
        ]
    ]

    products = order_data.get("products") or []
    default_hsn = order_data.get("hsn") or "8517"

    if not products:
        products = [{
            "name": "SevenXt Mobile Accessories & Components",
            "quantity": 1,
            "price": final_amount,
            "hsn": default_hsn
        }]

    grand_total = 0.0
    for idx, p in enumerate(products):
        p_name = p.get("name") or p.get("product_name") or p.get("title") or f"Item #{idx + 1}"
        hsn = p.get("hsn") or p.get("hsn_code") or default_hsn
        try:
            qty = int(p.get("quantity") or p.get("qty") or 1)
        except Exception:
            qty = 1

        try:
            item_price = float(p.get("price") or p.get("unit_price") or p.get("selling_price") or 0.0)
        except Exception:
            item_price = (final_amount / len(products)) if products else final_amount

        tot_item = round(item_price * qty, 2)
        grand_total += tot_item

        net_item = round(tot_item / 1.18, 2)
        unit_net = round(net_item / max(qty, 1), 2)
        tax_amt = round(tot_item - net_item, 2)

        desc_html = f"{p_name}<br/><font color='#4b5563' size=6>HSN: {hsn}</font>"

        if is_intra:
            tax_rate_str = "9%<br/>9%"
            tax_type_str = "CGST<br/>SGST"
            half_tax = round(tax_amt / 2, 2)
            other_half = round(tax_amt - half_tax, 2)
            tax_amt_str = f"{half_tax:.2f}<br/>{other_half:.2f}"
        else:
            tax_rate_str = "18%"
            tax_type_str = "IGST"
            tax_amt_str = f"{tax_amt:.2f}"

        table_data.append([
            Paragraph(str(idx + 1), style_cell_center),
            Paragraph(desc_html, style_cell_left),
            Paragraph(f"{unit_net:.2f}", style_cell_right),
            Paragraph(str(qty), style_cell_center),
            Paragraph(f"{net_item:.2f}", style_cell_right),
            Paragraph(tax_rate_str, style_cell_center),
            Paragraph(tax_type_str, style_cell_center),
            Paragraph(tax_amt_str, style_cell_right),
            Paragraph(f"{tot_item:.2f}", style_cell_right),
        ])

    # Reconcile shipping charges or discounts if products total differs from order total
    if final_amount > 0 and abs(final_amount - grand_total) >= 0.01:
        diff = round(final_amount - grand_total, 2)
        if diff > 0:
            # Shipping / Handling fee
            ship_net = round(diff / 1.18, 2)
            ship_tax = round(diff - ship_net, 2)
            if is_intra:
                s_tax_rate = "9%<br/>9%"
                s_tax_type = "CGST<br/>SGST"
                s_half_tax = round(ship_tax / 2, 2)
                s_tax_str = f"{s_half_tax:.2f}<br/>{round(ship_tax - s_half_tax, 2):.2f}"
            else:
                s_tax_rate = "18%"
                s_tax_type = "IGST"
                s_tax_str = f"{ship_tax:.2f}"

            table_data.append([
                Paragraph(str(len(products) + 1), style_cell_center),
                Paragraph("Shipping & Handling Charges<br/><font color='#4b5563' size=6>HSN: 996813</font>", style_cell_left),
                Paragraph(f"{ship_net:.2f}", style_cell_right),
                Paragraph("1", style_cell_center),
                Paragraph(f"{ship_net:.2f}", style_cell_right),
                Paragraph(s_tax_rate, style_cell_center),
                Paragraph(s_tax_type, style_cell_center),
                Paragraph(s_tax_str, style_cell_right),
                Paragraph(f"{diff:.2f}", style_cell_right),
            ])
            grand_total += diff
        else:
            # Discount
            disc = abs(diff)
            disc_net = round(disc / 1.18, 2)
            disc_tax = round(disc - disc_net, 2)
            if is_intra:
                d_tax_rate = "9%<br/>9%"
                d_tax_type = "CGST<br/>SGST"
                d_half = round(disc_tax / 2, 2)
                d_tax_str = f"-{d_half:.2f}<br/>-{round(disc_tax - d_half, 2):.2f}"
            else:
                d_tax_rate = "18%"
                d_tax_type = "IGST"
                d_tax_str = f"-{disc_tax:.2f}"

            table_data.append([
                Paragraph(str(len(products) + 1), style_cell_center),
                Paragraph("Promotional Discount", style_cell_left),
                Paragraph(f"-{disc_net:.2f}", style_cell_right),
                Paragraph("1", style_cell_center),
                Paragraph(f"-{disc_net:.2f}", style_cell_right),
                Paragraph(d_tax_rate, style_cell_center),
                Paragraph(d_tax_type, style_cell_center),
                Paragraph(d_tax_str, style_cell_right),
                Paragraph(f"-{disc:.2f}", style_cell_right),
            ])
            grand_total -= disc

    display_total = grand_total

    # TOTAL Row
    table_data.append([
        Paragraph("<b>TOTAL:</b>", style_bold),
        "", "", "", "", "", "", "",
        Paragraph(f"<b>{display_total:.2f}</b>", style_cell_bold_right)
    ])

    last_row_idx = len(table_data) - 1
    t_items = Table(table_data, colWidths=col_widths, repeatRows=1)
    t_items.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('SPAN', (0, last_row_idx), (7, last_row_idx)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.96, 0.96, 0.96)),
    ]))
    elements.append(t_items)
    elements.append(Spacer(1, 4 * mm))

    # 5. Amount in Words and Authorized Signatory Box
    words_str = number_to_words(display_total)
    words_html = (
        '<b>Amount in Words:</b><br/>'
        f'<b>{words_str}</b>'
    )
    sig_html = (
        '<b>For Sevenxt Electronic Pvt Ltd.:</b><br/><br/><br/><br/>'
        '<font size=7><b>Authorized Signatory</b></font>'
    )

    t_bottom_box = Table(
        [[Paragraph(words_html, style_normal), Paragraph(sig_html, style_title_right)]],
        colWidths=[120 * mm, 70 * mm]
    )
    t_bottom_box.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('LINEBEFORE', (1, 0), (1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_bottom_box)
    elements.append(Spacer(1, 2 * mm))

    # 6. Reverse charge note
    rc_html = '<font size=7>Whether tax is payable under reverse charge - No</font>'
    elements.append(Paragraph(rc_html, style_normal))

    doc.build(elements)
    logger.info(f"[AMAZON_INVOICE] Generated: {filepath}")
    return filename
