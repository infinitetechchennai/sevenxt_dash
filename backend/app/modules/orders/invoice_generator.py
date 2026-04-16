"""
Commercial Invoice PDF Generator — SevenXT
==========================================
Generates a stylized A4 invoice PDF.

FIXES applied in this version:
  1. Invoice Number now uses INV-YYYY-MM-XXXX (derived from order_id).
  2. GST calculated correctly:
       • Intra-state → CGST 9% + SGST 9%
       • Inter-state → IGST 18%
       • Subtotal = Total / 1.18 (price before GST)
  3. Correct seller GSTIN shown on invoice based on buyer's state.
  4. GST label rows adapt (intra shows CGST+SGST, inter shows IGST only).
"""

import os
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128

from app.modules.orders.order_id_generator import derive_invoice_number
from app.modules.orders.gst_utils import compute_gst

logger = logging.getLogger(__name__)


def generate_invoice_pdf(order, output_dir: str) -> str:
    """
    Generates a stylized Commercial Invoice PDF.

    Args:
        order:       SQLAlchemy Order ORM object  (or any object with matching attrs)
        output_dir:  Directory where the PDF should be saved

    Returns:
        Filename of the generated PDF (not the full path).
    """
    os.makedirs(output_dir, exist_ok=True)

    oid = getattr(order, 'order_id', str(order.id))
    display_order_id = getattr(order, "razorpay_order_id", None) or oid

    # ------------------------------------------------------------------ #
    #  FEATURE 2: Correct invoice number — INV-YYYY-MM-XXXX               #
    # ------------------------------------------------------------------ #
    invoice_number = derive_invoice_number(oid)
    # Invoice number is month-based, so ensure file names don't overwrite.
    filename = f"{invoice_number}_{oid}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=15 * mm,   bottomMargin=15 * mm,
    )
    elements = []
    styles = getSampleStyleSheet()

    style_normal      = styles['Normal']
    style_right       = ParagraphStyle('Right',       parent=styles['Normal'], alignment=TA_RIGHT)
    style_center      = ParagraphStyle('Center',      parent=styles['Normal'], alignment=TA_CENTER)
    style_center_small = ParagraphStyle('CenterSmall', parent=styles['Normal'],
                                        alignment=TA_CENTER, fontSize=8, textColor=colors.grey)

    # ------------------------------------------------------------------ #
    #  FEATURE 3 & 5: GST computation                                      #
    # ------------------------------------------------------------------ #
    buyer_state  = getattr(order, 'state', '') or ''
    # Fallback: if state field is empty, try to extract location from the full address
    if not buyer_state.strip():
        buyer_state = getattr(order, 'address', '') or ''
    final_amount = _get_float(getattr(order, 'amount', 0))
    gst          = compute_gst(total_amount=final_amount, buyer_state=buyer_state)

    seller_gstin = gst['seller_gstin']

    # ------------------------------------------------------------------ #
    #  1. Header (Logo & Invoice Meta)                                     #
    # ------------------------------------------------------------------ #
    company_info = f"""<font size=24 color="#e11d48"><b>SEVEN</b></font><font size=24><b>XT</b></font><br/><br/>
    <font size=9 color="grey">No.181/1, Old No.80/1, Swamy Naicken Street,<br/>
    Chintadripet, Chennai - 600002<br/>
    GSTIN: {seller_gstin}</font>"""

    date_str   = order.created_at.strftime('%B %d, %Y') if order.created_at else "N/A"
    pay_status = str(order.payment).upper() if order.payment else "UNPAID"
    pay_color  = "green" if ("PAID" in pay_status or "PREPAID" in pay_status) else "red"

    inv_meta = f"""<font size=32 color="#e5e7eb">INVOICE</font><br/>
    <font size=10 color="grey">Invoice Number</font><br/>
    <font size=12><b>{invoice_number}</b></font><br/><br/>
    <font size=10 color="grey">Order ID: {display_order_id}</font><br/>
    <font size=10 color="grey">Date: {date_str}</font><br/>
    <font color='{pay_color}'><b>{pay_status}</b></font>
    """

    t_head = Table(
        [[Paragraph(company_info, style_normal), Paragraph(inv_meta, style_right)]],
        colWidths=[110 * mm, 70 * mm],
    )
    t_head.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(t_head)
    elements.append(Spacer(1, 15 * mm))

    # ------------------------------------------------------------------ #
    #  2. Bill To & Order Details                                          #
    # ------------------------------------------------------------------ #
    products   = getattr(order, 'products', []) or []
    total_qty  = 0
    if isinstance(products, list):
        for p in products:
            try:
                total_qty += int(p.get('quantity') or p.get('qty') or 1)
            except Exception:
                pass
    else:
        total_qty = 1

    # GST type label for the invoice
    gst_type_label = "Intra-State (CGST + SGST)" if gst['gst_type'] == 'intra' else "Inter-State (IGST)"

    bill_to_html = f"""<font size=8 color="grey">BILL TO</font><br/>
    <font size=14><b>{order.customer_name or 'Customer'}</b></font><br/>
    <font size=10 color="#4b5563">
    {order.address or ''}<br/>
    {order.email or 'Email not provided'}<br/>
    {order.phone or ''}
    </font>"""

    order_details_html = f"""<font size=8 color="grey">ORDER DETAILS</font><br/>
    Order ID: <b>{display_order_id}</b><br/>
    Invoice No: <b>{invoice_number}</b><br/>
    Order Type: <b>{getattr(order, 'customer_type', 'B2C')}</b><br/>
    GST Type: <b>{gst_type_label}</b><br/>
    Total Items: <b>{total_qty}</b>"""

    t_cust = Table(
        [[Paragraph(bill_to_html, style_normal), Paragraph(order_details_html, style_right)]],
        colWidths=[90 * mm, 90 * mm],
    )
    t_cust.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(t_cust)
    elements.append(Spacer(1, 10 * mm))

    # ------------------------------------------------------------------ #
    #  3. AWB Barcode Box                                                  #
    # ------------------------------------------------------------------ #
    awb = getattr(order, 'awb_number', None)
    if awb:
        bc = code128.Code128(str(awb), barHeight=15 * mm, barWidth=1.5)
        bc_content = [
            Paragraph("<font size=9 color='grey'><b>AWB TRACKING NUMBER</b></font>", style_center),
            Spacer(1, 2 * mm),
            bc,
            Spacer(1, 2 * mm),
            Paragraph("Scan this barcode for shipment tracking", style_center_small),
        ]
        t_bc = Table([[bc_content]], colWidths=[180 * mm])
        t_bc.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.937, 0.965, 1.0)),
            ('ALIGN',       (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING',  (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
            ('TOPPADDING',   (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 15),
        ]))
        elements.append(t_bc)
        elements.append(Spacer(1, 10 * mm))

    # ------------------------------------------------------------------ #
    #  4. Items Table                                                       #
    # ------------------------------------------------------------------ #
    data       = [["#", "ITEMS", "HSN CODE", "QTY", "AMOUNT"]]
    total_calc = 0.0

    if isinstance(products, list) and products:
        for i, p in enumerate(products):
            desc  = p.get('name') or p.get('product_name') or 'Item'
            if len(desc) > 35:
                desc = desc[:32] + "..."
            hsn   = (p.get('hsn') or p.get('hsn_code') or
                     getattr(order, 'hsn', None) or 'N/A')
            try:
                qty = int(p.get('quantity') or 1)
            except Exception:
                qty = 1
            price = _get_float(p.get('price') or 0)
            amt   = qty * price
            total_calc += amt
            data.append([str(i + 1), desc, str(hsn), str(qty), f"Rs. {amt:.2f}"])
    else:
        amt = _get_float(order.amount)
        data.append(["1", "Order Items", "N/A", "1", f"Rs. {amt:.2f}"])
        total_calc = amt

    t_items = Table(data, colWidths=[10 * mm, 90 * mm, 30 * mm, 20 * mm, 30 * mm])
    t_items.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0),  (-1, 0),  colors.whitesmoke),
        ('TEXTCOLOR',    (0, 0),  (-1, 0),  colors.grey),
        ('FONTNAME',     (0, 0),  (-1, 0),  'Helvetica-Bold'),
        ('ALIGN',        (0, 0),  (-1, 0),  'LEFT'),
        ('ALIGN',        (-2, 0), (-1, -1), 'RIGHT'),
        ('ALIGN',        (2, 0),  (2, -1),  'CENTER'),
        ('BOTTOMPADDING',(0, 0),  (-1, 0),  8),
        ('TOPPADDING',   (0, 0),  (-1, 0),  8),
        ('FONTNAME',     (0, 1),  (-1, -1), 'Helvetica'),
        ('VALIGN',       (0, 0),  (-1, -1), 'MIDDLE'),
    ]))
    elements.append(t_items)
    elements.append(Spacer(1, 5 * mm))

    # ------------------------------------------------------------------ #
    #  5. Totals — correct GST breakdown                                   #
    # ------------------------------------------------------------------ #
    totals_data = []
    
    # If the sum of items doesn't match the final amount, show the difference (Discount/Shipping)
    if abs(total_calc - final_amount) > 0.01:
        totals_data.append(["Items Total (Inc. GST)", f"Rs. {total_calc:,.2f}"])
        if total_calc > final_amount:
            totals_data.append(["Discount", f"-Rs. {(total_calc - final_amount):,.2f}"])
        else:
            totals_data.append(["Shipping / Extra", f"+Rs. {(final_amount - total_calc):,.2f}"])

    totals_data.append(["Taxable Value", f"Rs. {gst['subtotal']:,.2f}"])

    if gst['gst_type'] == 'intra':
        totals_data.append([f"CGST ({gst['cgst_rate']:.0f}%)",
                             f"Rs. {gst['cgst_amount']:,.2f}"])
        totals_data.append([f"SGST ({gst['sgst_rate']:.0f}%)",
                             f"Rs. {gst['sgst_amount']:,.2f}"])
    else:
        totals_data.append([f"IGST ({gst['igst_rate']:.0f}%)",
                             f"Rs. {gst['igst_amount']:,.2f}"])

    totals_data.append([
        Paragraph("<b>Total Amount</b>", style_normal),
        Paragraph(f"<b><font color='#2563eb' size=14>Rs. {gst['total']:,.2f}</font></b>", style_right),
    ])

    t_totals = Table(totals_data, colWidths=[130 * mm, 50 * mm])
    t_totals.setStyle(TableStyle([
        ('ALIGN',     (0, 0),  (-1, -1), 'RIGHT'),
        ('TEXTCOLOR', (0, 0),  (0, -2),  colors.grey),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.whitesmoke),
        ('PADDING',   (0, 0),  (-1, -1), 6),
    ]))
    elements.append(t_totals)

    # ------------------------------------------------------------------ #
    #  Footer                                                              #
    # ------------------------------------------------------------------ #
    elements.append(Spacer(1, 20 * mm))
    elements.append(Paragraph(
        "<font color='grey' size=9>Thank you for your business!<br/>"
        "This is a computer generated invoice and does not require a physical signature.</font>",
        style_center,
    ))

    doc.build(elements)
    logger.info(f"[INVOICE] Generated: {filepath}")
    print(f"Generated Invoice: {filepath}")
    return filename


# ---------------------------------------------------------------------------
# Private helper
# ---------------------------------------------------------------------------

def _get_float(val) -> float:
    try:
        return float(str(val).replace(',', ''))
    except Exception:
        return 0.0
