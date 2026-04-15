"""
Order ID & Invoice Number Generator
====================================
Generates sequential, human-readable order IDs in the format:
    ORD-YYYY-MM-XXXX  (e.g., ORD-2026-04-0001)

The sequence resets every calendar month and is persisted in the
`order_sequence` table (year_month VARCHAR PK, last_seq INT).

Invoice numbers use the EXACT same sequence number:
    INV-YYYY-MM-XXXX  (e.g., INV-2026-04-0001)

Usage (inside any route / service):
    from app.modules.orders.order_id_generator import generate_order_id, derive_invoice_number

    order_id = generate_order_id(db)          # e.g. "ORD-2026-04-0001"
    invoice_no = derive_invoice_number(order_id)  # e.g. "INV-2026-04-0001"
"""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer, text
from app.database import Base
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Model — stored in the same DB as everything else
# ---------------------------------------------------------------------------

class OrderSequence(Base):
    """Tracks the last used sequence number per year-month bucket."""
    __tablename__ = "order_sequence"
    __table_args__ = {"extend_existing": True}

    year_month = Column(String(7), primary_key=True)  # e.g. "2026-04"
    last_seq = Column(Integer, nullable=False, default=0)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def generate_order_id(db: Session) -> str:
    """
    Atomically generate the next sequential Order ID for the current month.

    Strategy:
      1. Lock the row for this month (SELECT FOR UPDATE).
      2. Increment last_seq.
      3. Upsert back using raw SQL for cross-DB safety.
      4. Return the formatted Order ID string.

    Thread-safe: PostgreSQL row-level lock prevents duplicates under concurrent load.
    """
    now = datetime.utcnow()
    year_month = now.strftime("%Y-%m")   # "2026-04"
    year       = now.strftime("%Y")      # "2026"
    month      = now.strftime("%m")      # "04"

    try:
        # Upsert the counter row atomically (PostgreSQL ON CONFLICT)
        upsert_sql = text("""
            INSERT INTO order_sequence (year_month, last_seq)
            VALUES (:ym, 1)
            ON CONFLICT (year_month)
            DO UPDATE SET last_seq = order_sequence.last_seq + 1
            RETURNING last_seq
        """)
        result = db.execute(upsert_sql, {"ym": year_month})
        seq = result.scalar()
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("[ORDER_ID] Failed to generate sequential order ID")
        raise

    # Zero-pad to 4 digits; if seq somehow exceeds 9999 just let it grow
    seq_str = str(seq).zfill(4)
    order_id = f"ORD-{year}-{month}-{seq_str}"
    logger.info(f"[ORDER_ID] Generated: {order_id}")
    return order_id


def derive_invoice_number(order_id: str) -> str:
    """
    Convert an Order ID to its matching Invoice Number by replacing the
    'ORD-' prefix with 'INV-'.

    Examples:
        "ORD-2026-04-0001" → "INV-2026-04-0001"
        "ORD-2026-05-0023" → "INV-2026-05-0023"

    Falls back gracefully for legacy random-string order IDs:
        "order_SbJ3QBRhTjV3wA" → "INV-order_SbJ3QBRhTjV3wA"
    """
    if order_id and order_id.startswith("ORD-"):
        return "INV-" + order_id[4:]
    return f"INV-{order_id}"
