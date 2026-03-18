from sqlalchemy.orm import Session
from . import models, schemas
import uuid
from datetime import datetime, timedelta
import pandas as pd
import io

def ensure_datetime(date_val):
    if isinstance(date_val, str):
        try:
            return datetime.fromisoformat(date_val.replace('Z', '+00:00'))
        except:
            return None
    return date_val

def calculate_offer_prices(product: models.Product):
    """Calculates and updates offer prices - NO PRINT STATEMENTS for speed"""
    # Fix Timezone: Use UTC + 5:30 (IST) to match user input
    now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    
    # B2C Offer Logic
    discount_pct = 0.0
    b2c_offer_pct_val = product.b2c_active_offer if product.b2c_active_offer is not None else 0.0
    
    if b2c_offer_pct_val > 0:
        discount_pct = float(b2c_offer_pct_val)
    
    is_b2c_offer_active = False

    if discount_pct > 0:
        start_date = ensure_datetime(product.b2c_offer_start_date)
        end_date = ensure_datetime(product.b2c_offer_end_date)
        
        if start_date and end_date:
            # Check if offer has expired (past end date)
            if now > end_date:
                # Offer expired - clear it
                product.b2c_active_offer = 0.0
                product.b2c_offer_price = 0.0
                product.b2c_offer_start_date = None
                product.b2c_offer_end_date = None
                is_b2c_offer_active = False
            # Check if offer is currently active
            elif start_date <= now <= end_date:
                is_b2c_offer_active = True
            # Otherwise offer is scheduled for future - keep the data but don't activate yet
            else:
                is_b2c_offer_active = False
        else:
            # No dates specified - offer is always active
            is_b2c_offer_active = True
    
    if is_b2c_offer_active and discount_pct > 0:
        product.b2c_offer_price = product.b2c_price * (1 - discount_pct / 100.0)
    else:
        product.b2c_offer_price = 0.0

    # B2B Offer Logic
    discount_pct_b2b = 0.0
    b2b_offer_pct_val = product.b2b_active_offer if product.b2b_active_offer is not None else 0.0
    
    if b2b_offer_pct_val > 0:
        discount_pct_b2b = float(b2b_offer_pct_val)
    
    is_b2b_offer_active = False
    
    if discount_pct_b2b > 0:
        start_date_b2b = ensure_datetime(product.b2b_offer_start_date)
        end_date_b2b = ensure_datetime(product.b2b_offer_end_date)
        
        if start_date_b2b and end_date_b2b:
            # Check if offer has expired (past end date)
            if now > end_date_b2b:
                # Offer expired - clear it
                product.b2b_active_offer = 0.0
                product.b2b_offer_price = 0.0
                product.b2b_offer_start_date = None
                product.b2b_offer_end_date = None
                is_b2b_offer_active = False
            # Check if offer is currently active
            elif start_date_b2b <= now <= end_date_b2b:
                is_b2b_offer_active = True
            # Otherwise offer is scheduled for future - keep the data but don't activate yet
            else:
                is_b2b_offer_active = False
        else:
            # No dates specified - offer is always active
            is_b2b_offer_active = True
    
    if is_b2b_offer_active and discount_pct_b2b > 0:
        product.b2b_offer_price = product.b2b_price * (1 - discount_pct_b2b / 100.0)
    else:
        product.b2b_offer_price = 0.0


def get_products(db: Session, skip: int = 0, limit: int = 6000):
    try:
        products = db.query(models.Product).offset(skip).limit(limit).all()
        
        products_to_update = []
        for product in products:
            try:
                # Store original offer prices to detect changes
                original_b2c_offer_price = product.b2c_offer_price
                original_b2b_offer_price = product.b2b_offer_price
                
                calculate_offer_prices(product)
                
                # Check if offer prices changed (offer activated or deactivated)
                b2c_price_changed = original_b2c_offer_price != product.b2c_offer_price
                b2b_price_changed = original_b2b_offer_price != product.b2b_offer_price
                
                b2c_end = ensure_datetime(product.b2c_offer_end_date)
                b2b_end = ensure_datetime(product.b2b_offer_end_date)
                
                # Commit if: offer expired OR offer prices changed (activated/deactivated)
                if (b2c_end and b2c_end < datetime.now()) or \
                   (b2b_end and b2b_end < datetime.now()) or \
                   b2c_price_changed or b2b_price_changed:
                    products_to_update.append(product)
            except Exception:
                continue
        
        # Bulk commit all changes
        if products_to_update:
            for product in products_to_update:
                db.add(product)
            db.commit()
                
        return products
    except Exception as e:
        raise e

def get_product(db: Session, product_id: str):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product:
        # Store original offer prices to detect changes
        original_b2c_offer_price = product.b2c_offer_price
        original_b2b_offer_price = product.b2b_offer_price
        
        calculate_offer_prices(product)
        
        # Check if offer prices changed (offer activated or deactivated)
        b2c_price_changed = original_b2c_offer_price != product.b2c_offer_price
        b2b_price_changed = original_b2b_offer_price != product.b2b_offer_price
        
        # Commit if: offer expired OR offer prices changed
        if (product.b2c_offer_end_date and product.b2c_offer_end_date < datetime.now()) or \
           (product.b2b_offer_end_date and product.b2b_offer_end_date < datetime.now()) or \
           b2c_price_changed or b2b_price_changed:
            db.add(product)
            db.commit()
    return product

def create_product(db: Session, product: schemas.ProductCreate):
    if product.id:
        existing = db.query(models.Product).filter(models.Product.id == product.id).first()
        if existing:
            raise ValueError(f"Product with ID '{product.id}' already exists. Use update instead of create.")
        product_id = product.id
    else:
        product_id = f"prod_{uuid.uuid4().hex[:8]}"
    
    product_data = product.model_dump(exclude={'attributes', 'variants', 'id'}, by_alias=False)
    
    db_product = models.Product(
        id=product_id,
        **product_data
    )
    
    calculate_offer_prices(db_product)
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    for attr in product.attributes:
        db_attr = models.ProductAttribute(
            product_id=product_id,
            name=attr.name,
            value=attr.value
        )
        db.add(db_attr)
    
    for variant in product.variants:
        db_variant = models.ProductVariant(
            product_id=product_id,
            color=variant.color,
            color_code=variant.color_code,
            stock=variant.stock
        )
        db.add(db_variant)
        
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: str, product: schemas.ProductUpdate):
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    
    update_data = product.model_dump(exclude={'attributes', 'variants', 'id'}, exclude_unset=True, by_alias=False)
    
    for key, value in update_data.items():
        if hasattr(db_product, key):
            setattr(db_product, key, value)
            
    calculate_offer_prices(db_product)
    
    if product.attributes is not None:
        db.query(models.ProductAttribute).filter(models.ProductAttribute.product_id == product_id).delete()
        for attr in product.attributes:
            db_attr = models.ProductAttribute(
                product_id=product_id,
                name=attr.name,
                value=attr.value
            )
            db.add(db_attr)
            
    if product.variants is not None:
        db.query(models.ProductVariant).filter(models.ProductVariant.product_id == product_id).delete()
        for variant in product.variants:
            db_variant = models.ProductVariant(
                product_id=product_id,
                color=variant.color,
                color_code=variant.color_code,
                stock=variant.stock
            )
            db.add(db_variant)
            
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: str):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product:
        db.delete(db_product)
        db.commit()
        return True
    return False

def process_bulk_import(db: Session, file_contents: bytes, verbose: bool = False):
    """OPTIMIZED bulk import - NO PRINT STATEMENTS for maximum speed"""
    def safe_float(val, default=0.0):
        if pd.isna(val) or val == '' or val is None:
            return default
        try:
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                cleaned = val.strip().replace('₹', '').replace('$', '').replace(',', '').replace(' ', '')
                if cleaned == '' or cleaned == '-':
                    return default
                return float(cleaned)
            return float(val)
        except (ValueError, TypeError):
            return default
    
    def safe_int(val, default=0):
        if pd.isna(val) or val == '' or val is None:
            return default
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default
    
    def safe_str(val, default=''):
        if pd.isna(val) or val is None:
            return default
        return str(val).strip()
    
    def safe_date(val, default=None):
        """Parse date from Excel - handles Excel serial dates, ISO strings, and common formats"""
        if pd.isna(val) or val == '' or val is None:
            return default
        try:
            # If it's already a datetime object
            if isinstance(val, datetime):
                return val
            # If it's a pandas Timestamp, convert to datetime
            if hasattr(val, 'to_pydatetime'):
                return val.to_pydatetime()
            # If it's a string, try to parse it
            if isinstance(val, str):
                val = val.strip()
                if not val:
                    return default
                # Try common datetime formats (with time)
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%m/%d/%Y %H:%M:%S', '%d/%m/%Y %H:%M:%S']:
                    try:
                        return datetime.strptime(val, fmt)
                    except ValueError:
                        continue
                # Try common date formats (without time)
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y']:
                    try:
                        return datetime.strptime(val, fmt)
                    except ValueError:
                        continue
                # Try ISO format
                try:
                    return datetime.fromisoformat(val.replace('Z', '+00:00'))
                except:
                    pass
            # If it's a number (Excel serial date)
            if isinstance(val, (int, float)):
                # Excel serial date starts from 1900-01-01
                from datetime import timedelta
                base_date = datetime(1899, 12, 30)  # Excel's epoch
                return base_date + timedelta(days=float(val))
            return default
        except Exception:
            return default
    
    def get_color_hex(color_name):

        colors = {
            'red': '#FF0000', 'blue': '#0000FF', 'green': '#008000', 'yellow': '#FFFF00',
            'black': '#000000', 'white': '#FFFFFF', 'gray': '#808080', 'grey': '#808080',
            'orange': '#FFA500', 'purple': '#800080', 'pink': '#FFC0CB', 'brown': '#A52A2A',
            'cyan': '#00FFFF', 'magenta': '#FF00FF', 'lime': '#00FF00', 'navy': '#000080',
            'teal': '#008080', 'olive': '#808000', 'maroon': '#800000', 'aqua': '#00FFFF',
            'silver': '#C0C0C0', 'gold': '#FFD700', 'beige': '#F5F5DC', 'ivory': '#FFFFF0',
            'violet': '#EE82EE', 'indigo': '#4B0082', 'turquoise': '#40E0D0', 'coral': '#FF7F50',
            'salmon': '#FA8072', 'khaki': '#F0E68C', 'lavender': '#E6E6FA', 'plum': '#DDA0DD',
            'crimson': '#DC143C', 'mint': '#98FF98', 'peach': '#FFDAB9', 'rose': '#FF007F',
            'sky blue': '#87CEEB', 'dark blue': '#00008B', 'light blue': '#ADD8E6',
            'dark green': '#006400', 'light green': '#90EE90', 'forest green': '#228B22',
            'dark red': '#8B0000', 'light red': '#FF6B6B', 'bright red': '#FF0000',
            'dark gray': '#A9A9A9', 'light gray': '#D3D3D3', 'charcoal': '#36454F'
        }
        return colors.get(color_name.lower().strip(), '#000000')
    
    def get_value(row, possible_keys, default=None):
        for key in possible_keys:
            if key in row:
                val = row.get(key)
                if not pd.isna(val) and val != '' and val is not None:
                    return val
        return default
    
    try:
        import time
        start_time = time.time()
        
        # Read file
        df = None
        try:
            df = pd.read_excel(io.BytesIO(file_contents))
        except Exception:
            encodings_to_try = ['utf-8', 'utf-8-sig', 'latin1', 'iso-8859-1', 'cp1252']
            for encoding in encodings_to_try:
                try:
                    df = pd.read_csv(io.BytesIO(file_contents), encoding=encoding)
                    break
                except Exception:
                    if encoding == encodings_to_try[-1]:
                        raise Exception("Failed to read file")
        
        if df is None:
            raise Exception("Failed to read file")
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        df.columns = [c.lower().strip().replace(' ', '_') for c in df.columns]
        
        print(f"📊 Total rows in file: {len(df)}")
        print(f"📋 Columns found: {list(df.columns)[:10]}...")  # Show first 10 columns
        
        # STEP 1: Single query to fetch ALL existing products
        product_ids_in_file = []
        for _, row in df.iterrows():
            pid = safe_str(get_value(row, ['product_id', 'id', 'sku', 'product_code']))
            if pid:
                product_ids_in_file.append(pid)
        
        existing_products_dict = {}
        if product_ids_in_file:
            existing = db.query(models.Product).filter(models.Product.id.in_(product_ids_in_file)).all()
            existing_products_dict = {p.id: p for p in existing}
        
        # STEP 2: Prepare bulk data structures
        products_to_create = []
        products_to_update = []
        variants_to_create = []
        product_ids_to_update = []
        
        results = {"success": 0, "failed": 0, "errors": [], "created": 0, "updated": 0}
        now = datetime.now()
        
        # STEP 3: Parse all rows (in-memory, no DB access)
        for index, row in df.iterrows():
            try:
                name = safe_str(get_value(row, ['name', 'product_name', 'product', 'title']))
                if not name:
                    results["errors"].append(f"Row {index + 2}: No name")
                    results["failed"] += 1
                    continue
                
                category = safe_str(get_value(row, ['category', 'product_category', 'type'], 'Uncategorized'))
                b2c_price = safe_float(get_value(row, ['b2c_price', 'b2cprice', 'b2c', 'selling_price', 'price', 'retail_price', 'sp']))
                b2b_price = safe_float(get_value(row, ['b2b_price', 'b2bprice', 'b2b', 'wholesale_price', 'bulk_price', 'dealer_price']))
                mrp = safe_float(get_value(row, ['mrp', 'compare_at_price', 'original_price', 'actual_price', 'list_price', 'max_price']))
                b2c_discount = safe_float(get_value(row, ['b2c_discount', 'b2c_discount_%', 'b2cdiscount', 'discount', 'discount_%']))
                b2b_discount = safe_float(get_value(row, ['b2b_discount', 'b2b_discount_%', 'b2bdiscount', 'bulk_discount']))
                stock = safe_int(get_value(row, ['stock', 'quantity', 'qty', 'inventory']))
                description = safe_str(get_value(row, ['description', 'desc', 'product_description', 'details']))
                status = safe_str(get_value(row, ['status', 'product_status'], 'Draft'))
                image = safe_str(get_value(row, ['image', 'image_url', 'img', 'picture', 'photo']))
                rating = safe_float(get_value(row, ['rating', 'product_rating', 'stars']))
                # reviews = safe_int(get_value(row, ['reviews', 'review_count', 'num_reviews']))
                product_id = safe_str(get_value(row, ['product_id', 'id', 'sku', 'product_code']))
                
                sgst = safe_float(get_value(row, ['sgst', 'sgst_%', 'sgst_percentage', 'state_gst']))
                cgst = safe_float(get_value(row, ['cgst', 'cgst_%', 'cgst_percentage', 'central_gst']))
                hsn = safe_str(get_value(row, ['hsn', 'hsn_code', 'hsn_number']))
                # return_policy = safe_str(get_value(row, ['return_policy', 'returns', 'return', 'policy']))
                
                height = safe_float(get_value(row, ['height', 'height_(cm)', 'height_cm']))
                weight = safe_float(get_value(row, ['weight', 'weight_(kg)', 'weight_kg']))
                breadth = safe_float(get_value(row, ['breadth', 'breadth_(cm)', 'breadth_cm', 'width', 'width_(cm)']))
                length = safe_float(get_value(row, ['length', 'length_(cm)', 'length_cm']))
                
                
                b2c_offer = safe_float(get_value(row, ['b2c_offer_%', 'b2c_offer', 'b2coffer', 'offer_%', 'offer', 'b2c_active_offer_%']))
                b2b_offer = safe_float(get_value(row, ['b2b_offer_%', 'b2b_offer', 'b2boffer', 'bulk_offer', 'b2b_active_offer_%']))
                
                
                # Parse offer dates using safe_date to handle Excel date formats
                b2c_offer_start = safe_date(get_value(row, ['b2c_offer_start_date', 'b2c_start_date', 'b2c_offer_start']))
                b2c_offer_end = safe_date(get_value(row, ['b2c_offer_end_date', 'b2c_end_date', 'b2c_offer_end']))
                b2b_offer_start = safe_date(get_value(row, ['b2b_offer_start_date', 'b2b_start_date', 'b2b_offer_start']))
                b2b_offer_end = safe_date(get_value(row, ['b2b_offer_end_date', 'b2b_end_date', 'b2b_offer_end']))

                
                # Parse variants
                variants_str = safe_str(get_value(row, ['variants_(colors)', 'variants', 'colors', 'variant_colors', 'variants_colors', 'color_variants', 'product_variants']))
                variants = []
                if variants_str:
                    for part in variants_str.split(','):
                        part = part.strip()
                        if part and '(' in part and ')' in part:
                            color_name = part.split('(')[0].strip()
                            stock_str = part.split('(')[1].split(')')[0].replace('Stock:', '').replace('stock:', '').strip()
                            try:
                                variants.append({
                                    'color': color_name,
                                    'color_code': get_color_hex(color_name),
                                    'stock': int(float(stock_str))
                                })
                            except ValueError:
                                pass
                
                # Calculate offer prices
                b2c_offer_price = b2c_price * (1 - b2c_offer / 100.0) if b2c_offer > 0 else 0.0
                b2b_offer_price = b2b_price * (1 - b2b_offer / 100.0) if b2b_offer > 0 else 0.0
                
                # DEBUG: Print offer data for first few products
                if index < 3:
                    print(f"\n🔍 DEBUG Row {index + 2} - {name}:")
                    print(f"  B2C Offer: {b2c_offer}% | Start: {b2c_offer_start} | End: {b2c_offer_end}")
                    print(f"  B2B Offer: {b2b_offer}% | Start: {b2b_offer_start} | End: {b2b_offer_end}")
                    print(f"  B2C Offer Price: {b2c_offer_price} | B2B Offer Price: {b2b_offer_price}")
                
                product_data = {
                    'name': name,
                    'category': category,
                    'b2c_price': b2c_price,
                    'compare_at_price': mrp,
                    'b2b_price': b2b_price,
                    'b2c_discount': b2c_discount,
                    'b2b_discount': b2b_discount,
                    'stock': stock,
                    'description': description or None,
                    'status': status if status in ['Active', 'Draft', 'Archived'] else 'Draft',
                    'image': image or None,
                    'rating': rating,
                    # 'reviews': reviews,  # Commented out - field removed from model
                    'b2c_active_offer': b2c_offer,
                    'b2b_active_offer': b2b_offer,
                    'b2c_offer_price': b2c_offer_price,
                    'b2b_offer_price': b2b_offer_price,
                    'b2c_offer_start_date': b2c_offer_start or None,
                    'b2c_offer_end_date': b2c_offer_end or None,
                    'b2b_offer_start_date': b2b_offer_start or None,
                    'b2b_offer_end_date': b2b_offer_end or None,
                    'sgst': sgst,
                    'cgst': cgst,
                    'hsn': hsn or None,
                    # 'return_policy': return_policy or None,  # Commented out - field removed from model
                    'height': height,
                    'weight': weight,
                    'breadth': breadth,
                    'length': length,
                    'updated_at': now
                }
                
                # Update or Create?
                if product_id and product_id in existing_products_dict:
                    product_data['id'] = product_id
                    products_to_update.append(product_data)
                    product_ids_to_update.append(product_id)
                    for v in variants:
                        variants_to_create.append({'product_id': product_id, **v})
                    results["updated"] += 1
                else:
                    if not product_id:
                        product_id = f"prod_{uuid.uuid4().hex[:8]}"
                    product_data['id'] = product_id
                    product_data['created_at'] = now
                    products_to_create.append(product_data)
                    for v in variants:
                        variants_to_create.append({'product_id': product_id, **v})
                    results["created"] += 1
                
                results["success"] += 1
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Row {index + 2}: {str(e)}")
        
        # STEP 4: BULK DATABASE OPERATIONS
        if product_ids_to_update:
            db.query(models.ProductVariant).filter(
                models.ProductVariant.product_id.in_(product_ids_to_update)
            ).delete(synchronize_session=False)
        
        if products_to_create:
            db.bulk_insert_mappings(models.Product, products_to_create)
        
        if products_to_update:
            db.bulk_update_mappings(models.Product, products_to_update)
        
        if variants_to_create:
            db.bulk_insert_mappings(models.ProductVariant, variants_to_create)
        
        db.commit()
        
        elapsed = time.time() - start_time
        
        # Only print summary
        print(f"\n⚡ COMPLETED IN {elapsed:.2f}s | ✅ {results['success']} ({results['created']} created, {results['updated']} updated) | ❌ {results['failed']} failed | Speed: {results['success'] / elapsed:.0f} products/sec\n")
        
        return results
        
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        raise Exception(f"Import failed: {str(e)}")
