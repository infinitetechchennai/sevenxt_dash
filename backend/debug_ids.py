
from app.database import SessionLocal
from app.modules.reviews.models import ProductReview
from app.modules.products.models import Product

db = SessionLocal()
reviews = db.query(ProductReview).all()
print(f"Total reviews: {len(reviews)}")
for r in reviews:
    print(f"Review ID: {r.id}, Product ID: {r.product_id}, Type: {type(r.product_id)}, Comment: {r.comment}")

products = db.query(Product).all()
print(f"\nTotal products: {len(products)}")
for p in products:
    print(f"Product ID: {p.id}, Type: {type(p.id)}, Name: {p.name}")
db.close()
