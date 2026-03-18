
import os
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128, qr
from reportlab.graphics.shapes import Drawing

logger = logging.getLogger(__name__)

def generate_invoice_pdf(order, output_dir):
    """
    Generates a stylized Commercial Invoice PDF matching the frontend design.
    Features: Red Logo, Blue Barcode Box, 2-Column Details, Clean Table.
    """
    os.makedirs(output_dir, exist_ok=True)
    oid = getattr(order, 'order_id', str(order.id))
    filename = f"INV-{oid}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=A4, 
                            rightMargin=15*mm, leftMargin=15*mm, 
                            topMargin=15*mm, bottomMargin=15*mm)
    elements = []
    styles = getSampleStyleSheet()
    
    style_normal = styles['Normal']
    style_right = ParagraphStyle('Right', parent=styles['Normal'], alignment=TA_RIGHT)
    style_center = ParagraphStyle('Center', parent=styles['Normal'], alignment=TA_CENTER)
    style_center_small = ParagraphStyle('CenterSmall', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, textColor=colors.grey)

    # 1. Header (Logo & Invoice Meta)
    # ----------------------------
    company_info = """<font size=24 color="#e11d48"><b>SEVEN</b></font><font size=24><b>XT</b></font><br/><br/>
    <font size=9 color="grey">123 Innovation Park, Tech City<br/>
    No.181/1, Old No.80/1, Swamy Naicken Street,<br/>
    Chintadripet Chennai 600002<br/>
    GSTIN: 33ABLCS5237N1ZU</font>"""
    
    date_str = order.created_at.strftime('%B %d, %Y') if order.created_at else "N/A"
    pay_status = str(order.payment).upper() if order.payment else "UNPAID"
    pay_color = "green" if "PAID" in pay_status or "PREPAID" in pay_status else "red"
    
    inv_meta = f"""<font size=32 color="#e5e7eb">INVOICE</font><br/>
    <font size=10 color="grey">Invoice Number</font><br/>
    <font size=12><b>INV-{oid}</b></font><br/><br/>
    <font size=10 color="grey">Date: {date_str}</font><br/>
    <font color='{pay_color}'><b>{pay_status}</b></font>
    """
    
    t_head = Table([[Paragraph(company_info, style_normal), Paragraph(inv_meta, style_right)]], colWidths=[110*mm, 70*mm])
    t_head.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(t_head)
    elements.append(Spacer(1, 15*mm))
    
    # 2. Bill To & Order Details (2 Columns)
    # ----------------------------
    bill_to_html = f"""<font size=8 color="grey">BILL TO</font><br/>
    <font size=14><b>{order.customer_name or 'Customer'}</b></font><br/>
    <font size=10 color="#4b5563">
    {order.address or ''}<br/>
    {order.email or 'Email not provided'}<br/>
    {order.phone or ''}
    </font>"""
    
    # Calculate Total Items
    products = getattr(order, 'products', []) or []
    total_qty = 0
    if isinstance(products, list):
        for p in products:
            try: total_qty += int(p.get('quantity') or p.get('qty') or 1)
            except: pass
    else:
        total_qty = 1

    order_details_html = f"""<font size=8 color="grey">ORDER DETAILS</font><br/>
    Order ID: <b>{oid}</b><br/>
    Order Type: <b>{getattr(order, 'customer_type', 'B2C')}</b><br/>
    Total Items: <b>{total_qty}</b>"""
    
    t_cust = Table([[Paragraph(bill_to_html, style_normal), Paragraph(order_details_html, style_right)]], colWidths=[90*mm, 90*mm])
    t_cust.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(t_cust)
    elements.append(Spacer(1, 10*mm))
    
    # 3. AWB Barcode Box (Blue Background)
    # ----------------------------
    awb = getattr(order, 'awb_number', None)
    if awb:
        bc = code128.Code128(str(awb), barHeight=15*mm, barWidth=1.5)
        
        bc_content = [
            Paragraph("<font size=9 color='grey'><b>AWB TRACKING NUMBER</b></font>", style_center),
            Spacer(1, 2*mm),
            bc,  # Direct barcode object, no Drawing wrapper needed
            Spacer(1, 2*mm),
            Paragraph("Scan this barcode for shipment tracking", style_center_small)
        ]
        
        t_bc = Table([[bc_content]], colWidths=[180*mm])
        # Light Blue Background: #eff6ff (RGB: 239, 246, 255) -> (0.937, 0.965, 1.0)
        t_bc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.Color(0.937, 0.965, 1.0)),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 20),
            ('RIGHTPADDING', (0,0), (-1,-1), 20),
            ('TOPPADDING', (0,0), (-1,-1), 15),
            ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ]))
        elements.append(t_bc)
        elements.append(Spacer(1, 10*mm))

    # 4. Items Table
    # ----------------------------
    data = [["#", "ITEMS", "HSN CODE", "QTY", "AMOUNT"]]
    
    total_calc = 0.0
    
    def get_float(val):
        try: return float(str(val).replace(',', ''))
        except: return 0.0

    if isinstance(products, list) and products:
        for i, p in enumerate(products):
             desc = p.get('name') or p.get('product_name') or 'Item'
             if len(desc) > 35: desc = desc[:32] + "..."
             hsn = p.get('hsn') or p.get('hsn_code') or getattr(order, 'hsn', None) or 'N/A'
             try: qty = int(p.get('quantity') or 1)
             except: qty = 1
             price = get_float(p.get('price') or 0)
             amt = qty * price
             total_calc += amt
             
             data.append([str(i+1), desc, str(hsn), str(qty), f"Rs. {amt:.2f}"])
    else:
        amt = get_float(order.amount)
        data.append(["1", "Order Items", "N/A", "1", f"Rs. {amt:.2f}"])
        total_calc = amt

    t_items = Table(data, colWidths=[10*mm, 90*mm, 30*mm, 20*mm, 30*mm])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('TEXTCOLOR', (0,0), (-1,0), colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,0), 'LEFT'),
        ('ALIGN', (-2,0), (-1,-1), 'RIGHT'),
        ('ALIGN', (2,0), (2,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t_items)
    elements.append(Spacer(1, 5*mm))
    
    # 5. Totals
    # ----------------------------
    final_amount = get_float(order.amount)
    if final_amount == 0: final_amount = total_calc
    
    sgst_p = get_float(order.sgst_percentage)
    cgst_p = get_float(order.cgst_percentage)
    tax_rate = (sgst_p + cgst_p) / 100.0
    
    if tax_rate > 0: subtotal = final_amount / (1 + tax_rate)
    else: subtotal = final_amount
        
    sgst_amt = subtotal * (sgst_p / 100.0)
    cgst_amt = subtotal * (cgst_p / 100.0)
    
    totals_data = [
        ["Subtotal", f"Rs. {subtotal:,.2f}"],
        [f"SGST ({sgst_p}%)", f"Rs. {sgst_amt:,.2f}"],
        [f"CGST ({cgst_p}%)", f"Rs. {cgst_amt:,.2f}"],
        [Paragraph("<b>Total Amount</b>", style_normal), Paragraph(f"<b><font color='#2563eb' size=14>Rs. {final_amount:,.2f}</font></b>", style_right)]
    ]
    
    t_totals = Table(totals_data, colWidths=[130*mm, 50*mm])
    t_totals.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('TEXTCOLOR', (0,0), (0,-2), colors.grey),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.whitesmoke),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_totals)
    
    # QR Code Section (Order Summary) - TEMPORARILY DISABLED FOR DEBUGGING
    # elements.append(Spacer(1, 10*mm))
    # 
    # qr_lines = [f"Order: {oid}", f"Date: {date_str}"]
    # qr_lines.append("Items:")
    # if isinstance(products, list):
    #      for p in products:
    #          p_name = p.get('name') or p.get('product_name') or 'Item'
    #          try: p_qty = int(p.get('quantity') or p.get('qty') or 1)
    #          except: p_qty = 1
    #          qr_lines.append(f"- {str(p_name)[:20]} x{p_qty}")
    # qr_lines.append(f"Total: {final_amount}")
    # 
    # qr_data = "\n".join(qr_lines)
    # 
    # try:
    #     qr_w = qr.QrCodeWidget(qr_data)
    #     qr_sz = 25*mm
    #     
    #     # Use transform matrix approach (same as label_generator.py)
    #     d_qr = Drawing(qr_sz, qr_sz, transform=[qr_sz/100.0, 0, 0, qr_sz/100.0, 0, 0])
    #     d_qr.add(qr_w)
    #     
    #     # QR Table
    #     t_qr = Table([[d_qr, Paragraph("<b>Scan for Order Details</b>", style_center_small)]], colWidths=[30*mm, 40*mm])
    #     t_qr.setStyle(TableStyle([
    #         ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    #         ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    #     ]))
    #     elements.append(t_qr)
    # except Exception as e:
    #     logger.error(f"QR Generation Error: {e}")
    #     print(f"QR Generation Error: {e}")
    
    # Footer
    elements.append(Spacer(1, 20*mm))
    elements.append(Paragraph("<font color='grey' size=9>Thank you for your business!<br/>This is a computer generated invoice and does not require a physical signature.</font>", style_center))

    doc.build(elements)
    print(f"Generated Invoice: {filepath}")
    return filename
