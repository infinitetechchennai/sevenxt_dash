
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing

from app.modules.orders.order_id_generator import derive_invoice_number
from app.modules.orders.gst_utils import compute_gst

# 100mm x 150mm
PAGE_WIDTH = 100 * mm
PAGE_HEIGHT = 150 * mm

def generate_invoice_label_pdf(order_data, output_dir):
    """
    Generates a shipping label PDF with a clean layout: 
    Centered Barcode, Full-width Address, QR Strip, and Compact Footer.
    Removes the dummy carrier boxes (SUR, Station/Sector).
    """
    os.makedirs(output_dir, exist_ok=True)
    oid = order_data.get('order_id') or str(order_data.get('id', ''))
    display_order_id = order_data.get("razorpay_order_id") or oid
    filename = f"label_{oid}.pdf"
    filepath = os.path.join(output_dir, filename)

    buyer_state = " ".join([
        str(order_data.get("state") or ""),
        str(order_data.get("city") or ""),
        str(order_data.get("address") or ""),
    ]).strip()
    final_amount = float(order_data.get("amount") or 0) if str(order_data.get("amount") or "").strip() else 0.0
    gst = compute_gst(total_amount=final_amount, buyer_state=buyer_state)
    seller_gstin = gst.get("seller_gstin") or "33ABLCS5237N1ZU"
    invoice_number = derive_invoice_number(oid)
    
    c = canvas.Canvas(filepath, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    
    # Draw Outer Border
    c.setLineWidth(1)
    c.rect(2*mm, 2*mm, PAGE_WIDTH-4*mm, PAGE_HEIGHT-4*mm)
    
    # ==========================
    # 1. TOP HEADER (40mm)
    # ==========================
    y_start = PAGE_HEIGHT - 5*mm
    
    # Centered Barcode
    awb = str(order_data.get('awb_number', ''))
    if awb:
        barcode = code128.Code128(awb, barHeight=16*mm, barWidth=1.5)
        
        bc_width = barcode.width
        x_centered = (PAGE_WIDTH - bc_width) / 2
        
        barcode.drawOn(c, x_centered, y_start - 20*mm)
        
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(PAGE_WIDTH/2, y_start - 25*mm, f"AWB {awb}")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, y_start - 35*mm, "Ship To:")
    
    y = y_start - 40*mm 
    
    # ==========================
    # 2. ADDRESS SECTION (35mm)
    # ==========================
    
    # Full Width Address
    c.setFont("Helvetica-Bold", 12)
    cust_name = (order_data.get('customer') or '').upper()[:30]
    c.drawString(5*mm, y, cust_name)
    y -= 5*mm
    
    c.setFont("Helvetica", 10)
    address = (order_data.get('address') or '').upper()
    
    # Manual wrap (wider now)
    import textwrap
    lines = textwrap.wrap(address, width=45)
    curr_y = y
    for line in lines[:4]:
        c.drawString(5*mm, curr_y, line)
        curr_y -= 4*mm
        
    city_pin = f"{order_data.get('city', '')} {order_data.get('pincode', '')}".upper()
    c.drawString(5*mm, curr_y, city_pin)
    curr_y -= 4*mm
    c.drawString(5*mm, curr_y, (order_data.get('state') or '').upper())
    curr_y -= 5*mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(5*mm, curr_y, f"Ph: {order_data.get('phone', '')}")
    
    # Removed Sort Box
    
    y = curr_y - 8*mm
    
    # Separator
    c.line(2*mm, y, PAGE_WIDTH-2*mm, y)
    y -= 3*mm
    
    # ==========================
    # 3. QR CODES (Strip)
    # ==========================
    qr_size = 20*mm
    gap = 5*mm
    total_qr_w = 3*qr_size + 2*gap
    start_x = (PAGE_WIDTH - total_qr_w) / 2
    
    def draw_qr_scaled(content, x, y, size):
        qr = QrCodeWidget(content)
        b = qr.getBounds()
        w = b[2]-b[0]
        h = b[3]-b[1]
        sc_x = size/w
        sc_y = size/h
        d = Drawing(size, size, transform=[sc_x,0,0,sc_y,0,0])
        d.add(qr)
        d.drawOn(c, x, y)
        
    qr_y = y - qr_size
    # QR 1
    draw_qr_scaled("123456789", start_x, qr_y, qr_size)
    # QR 2
    if awb:
        draw_qr_scaled(awb, start_x + qr_size + gap, qr_y, qr_size)
    else:
        draw_qr_scaled("NO AWB", start_x + qr_size + gap, qr_y, qr_size)
    # QR 3
    draw_qr_scaled(display_order_id, start_x + 2*qr_size + 2*gap, qr_y, qr_size)
    
    y = qr_y - 3*mm
    
    # Separator
    c.line(2*mm, y, PAGE_WIDTH-2*mm, y)
    y -= 4*mm
    
    # ==========================
    # 4. FOOTER (Shipped By + Table)
    # ==========================
    c.setFont("Helvetica-Bold", 7)
    c.drawString(5*mm, y, "Shipped By: Sevenxt Electronic Pvt Ltd.")
    y -= 3*mm
    c.setFont("Helvetica", 6)
    # Wrap return address into multiple lines
    c.drawString(5*mm, y, "Return Address: Acien Infotech No.181/1 - Second Floor,")
    y -= 2.5*mm
    c.drawString(5*mm, y, "Swamy Naicken Street, Chintadripet Chennai Tamil Nadu 600002 India")
    y -= 2.5*mm
    c.setFont("Helvetica-Oblique", 6)
    c.drawString(5*mm, y, "Goods sold are intended for end user consumption.")
    y -= 4*mm
    
    # TABLE
    cols = [5*mm, 15*mm, 20*mm, 15*mm, 15*mm, 25*mm]
    headers = ["#", "SELLER", "GSTIN", "INV#", "DATE", "ITEM"]
    
    table_x = 3*mm
    row_h = 5*mm
    
    # Draw Headers
    c.setLineWidth(0.5)
    current_x = table_x
    c.rect(table_x, y - row_h, sum(cols), row_h)
    
    for i, w in enumerate(cols):
        if i < len(cols):
            c.line(current_x + w, y, current_x + w, y - row_h)
        c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(current_x + w/2, y - 3.5*mm, headers[i])
        current_x += w
        
    y -= row_h
    
    # Draw Values
    c.rect(table_x, y - row_h, sum(cols), row_h)
    current_x = table_x
    
    inv_val = invoice_number
    date_val = str(order_data.get('date', ''))[:10]
    vals = ["1", "SevenXt", seller_gstin, inv_val, date_val, "ELEC/ACC"]
    
    for i, w in enumerate(cols):
         if i < len(cols):
            c.line(current_x + w, y, current_x + w, y - row_h)
         c.setFont("Helvetica", 6)
         val = vals[i]
         if len(val) > 12: val = val[:10] + ".."
         c.drawCentredString(current_x + w/2, y - 3.5*mm, val)
         current_x += w

    c.save()
    return filename
