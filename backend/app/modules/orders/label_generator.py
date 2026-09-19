
"""
SevenXt Label & Invoice Generator
=================================
Generates the Amazon-style Tax Invoice / Bill of Supply PDF with SevenXt branding.
"""

from app.modules.orders.invoice_generator import generate_invoice_pdf

def generate_invoice_label_pdf(order_data, output_dir):
    """
    Generates Amazon-style Tax Invoice / Bill of Supply PDF for shipping/packaging.
    Saves as label_{oid}.pdf in output_dir and returns filename.
    """
    return generate_invoice_pdf(order_data, output_dir, prefix="label")

