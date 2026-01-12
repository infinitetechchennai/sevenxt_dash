import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.modules.exchanges.models import Exchange

print("=" * 70)
print("CHECKING EXCHANGE DATABASE STATUS")
print("=" * 70)

db = SessionLocal()

try:
    # Check if exchange exists
    awb = "84927910000910"
    exchange = db.query(Exchange).filter(Exchange.return_awb_number == awb).first()
    
    if not exchange:
        print(f"\n❌ NO EXCHANGE FOUND with AWB: {awb}")
        print("\n📋 Available exchanges with return AWBs:")
        exchanges = db.query(Exchange).filter(Exchange.return_awb_number != None).limit(5).all()
        for exc in exchanges:
            print(f"   - Exchange #{exc.id}: AWB {exc.return_awb_number}, Attempts: {exc.delivery_attempts if hasattr(exc, 'delivery_attempts') else 'N/A'}")
        
        if exchanges:
            print(f"\n💡 TIP: Use one of these AWB numbers instead:")
            print(f"   {exchanges[0].return_awb_number}")
    else:
        print(f"\n✅ EXCHANGE FOUND!")
        print(f"   Exchange ID: {exchange.id}")
        print(f"   Order ID: {exchange.order_id}")
        print(f"   Return AWB: {exchange.return_awb_number}")
        print(f"   Status: {exchange.status}")
        print(f"   Delivery Attempts: {exchange.delivery_attempts if hasattr(exchange, 'delivery_attempts') else 'Column not found'}")
        print(f"   Return Delivery Status: {exchange.return_delivery_status}")
        
        if hasattr(exchange, 'delivery_attempts'):
            if exchange.delivery_attempts >= 3:
                print(f"\n⚠️  WARNING: Already has {exchange.delivery_attempts} attempts!")
                print("   Email should have been sent already.")
            else:
                print(f"\n📊 Current attempts: {exchange.delivery_attempts}")
                print(f"   Need {3 - exchange.delivery_attempts} more 'Attempt Fail' webhooks to trigger email.")
        else:
            print("\n❌ ERROR: delivery_attempts column doesn't exist!")
            print("   Run the SQL migration first!")
            
finally:
    db.close()

print("\n" + "=" * 70)
