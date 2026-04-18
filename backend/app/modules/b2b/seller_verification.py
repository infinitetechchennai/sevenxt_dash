import re
import io
import PyPDF2
from typing import Dict, Tuple, Optional

# --- REGEX PATTERNS ---
GSTIN_PATTERN = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Zz][A-Z\d]{1}\b", re.IGNORECASE)
PAN_PATTERN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]{1}\b", re.IGNORECASE)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Safely extracts text from a PDF memory bytes stream"""
    text = ""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as e:
        print(f"PDF Extraction Error: {e}")
    return text.upper()

def extract_gstin(text: str) -> Optional[str]:
    """Finds the first valid GSTIN in the text"""
    match = GSTIN_PATTERN.search(text)
    return match.group(0) if match else None

def extract_pan(text: str) -> Optional[str]:
    """Finds the first valid PAN in the text"""
    match = PAN_PATTERN.search(text)
    return match.group(0) if match else None

def validate_seller_documents(
    gst_pdf_bytes: bytes, 
    pan_pdf_bytes: bytes, 
    user_gstin: str, 
    user_pan: str
) -> Dict[str, str]:
    """
    Core Business Logic for Mock B2B Document Verification
    """
    user_gstin = user_gstin.strip().upper()
    user_pan = user_pan.strip().upper()

    # 1. Basic Format Validation
    if not GSTIN_PATTERN.match(user_gstin):
        return {"status": "failed", "reason": "invalid gst format"}
    if not PAN_PATTERN.match(user_pan):
        return {"status": "failed", "reason": "invalid pan format"}

    # 2. Extract PAN out of the handwritten user GSTIN
    expected_pan_from_gstin = user_gstin[2:12]
    if user_pan != expected_pan_from_gstin:
        return {"status": "failed", "reason": "pan mismatch with gstin structure"}

    # 3. PDF Extraction Validation (If achievable)
    gst_text = extract_text_from_pdf(gst_pdf_bytes)
    pan_text = extract_text_from_pdf(pan_pdf_bytes)

    extracted_gstin = extract_gstin(gst_text)
    extracted_pan = extract_pan(pan_text)

    # 4. Strict Document Checking
    if extracted_gstin and extracted_gstin != user_gstin:
        return {"status": "failed", "reason": "uploaded gst certificate does not match entered gstin"}
    
    if extracted_pan and extracted_pan != user_pan:
        return {"status": "failed", "reason": "uploaded pan card does not match entered pan"}

    # If it passes mock validation cleanly
    return {"status": "verified", "reason": "success"}
