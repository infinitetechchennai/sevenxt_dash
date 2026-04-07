import razorpay
from sqlalchemy.orm import Session
from . import models, schemas
from app.config import settings
from fastapi import HTTPException

# ✅ CORRECTED: Initializing with Razorpay credentials, not Twilio
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)) 

def get_all_transactions(db: Session):
    """Fetches all transactions from the transactions table"""
    return db.query(models.Transaction).order_by(models.Transaction.created_at.desc()).all()

def verify_payment(db: Session, data: schemas.PaymentVerifyRequest):
    """Verifies the Razorpay signature before marking payment as SUCCESS"""
    params_dict = {
        'razorpay_order_id': data.razorpay_order_id,
        'razorpay_payment_id': data.razorpay_payment_id,
        'razorpay_signature': data.razorpay_signature
    }

    try:
        # Verify the authenticity of the payment signature
        client.utility.verify_payment_signature(params_dict)
        
        # Check if transaction exists, otherwise create it
        txn = db.query(models.Transaction).filter(
            models.Transaction.razorpay_order_id == data.razorpay_order_id
        ).first()

        if not txn:
            txn = models.Transaction(
                razorpay_order_id=data.razorpay_order_id,
                internal_order_id=data.internal_order_id,
                user_email=data.user_email,
                amount=data.amount
            )
            db.add(txn)

        # Update details and set status to SUCCESS
        txn.razorpay_payment_id = data.razorpay_payment_id
        txn.razorpay_signature = data.razorpay_signature
        txn.status = "SUCCESS"
        
        db.commit()
        db.refresh(txn)
        return txn

    except Exception as e:
        # Mark as FAILED in database if signature check fails
        db_txn = db.query(models.Transaction).filter(
            models.Transaction.razorpay_order_id == data.razorpay_order_id
        ).first()
        if db_txn:
            db_txn.status = "FAILED"
            db.commit()
        
        raise HTTPException(status_code=400, detail="Payment verification failed")