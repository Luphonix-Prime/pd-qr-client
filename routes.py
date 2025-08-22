from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import current_user
from datetime import datetime, date
from app import app, db
from models import User, Factory, Product, Batch, ProductCode, FirstLevelCode, SecondLevelCode, ShipperCode, ShipperProduct, Stock
from replit_auth import require_login, make_replit_blueprint
from utils import generate_qr_code, generate_batch_id, generate_product_id, generate_factory_id, export_to_excel

app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@require_login
def dashboard():
    # Get dashboard statistics
    total_products = Product.query.count()
    total_batches = Batch.query.count()
    total_factories = Factory.query.count()
    
    # Recent batches
    recent_batches = Batch.query.order_by(Batch.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         total_products=total_products,
                         total_batches=total_batches,
                         total_factories=total_factories,
                         recent_batches=recent_batches)

@app.route('/batch-management')
@require_login
def batch_management():
    page = request.args.get('page', 1, type=int)
    product_filter = request.args.get('product_id', '')
    
    # Build query with stock information
    query = Batch.query.join(Product).join(Factory)
    if product_filter:
        query = query.filter(Batch.product_id == product_filter)
    
    batches = query.order_by(Batch.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    products = Product.query.all()
    factories = Factory.query.all()
    
    # Calculate total stock for each batch
    for batch in batches.items:
        stock_total = db.session.query(db.func.sum(Stock.units)).filter_by(batch_id=batch.id).scalar() or 0
        batch.total_stock = stock_total
    
    # Format today's date for batch number
    today_formatted = datetime.now().strftime('%Y%m%d')
    
    return render_template('batch_management.html', 
                         batches=batches, 
                         products=products,
                         factories=factories,
                         product_filter=product_filter,
                         today_formatted=today_formatted)

@app.route('/add-batch', methods=['POST'])
@require_login
def add_batch():
    try:
        batch_id = generate_batch_id()
        batch = Batch(
            id=batch_id,
            batch_no=request.form['batch_no'],
            product_id=request.form['product_id'],
            factory_id=request.form['factory_id'],
            mfg_date=datetime.strptime(request.form['mfg_date'], '%Y-%m-%d').date(),
            expiry_date=datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date(),
            qa_status=request.form.get('qa_status', 'OK'),
            responded_by=current_user.first_name or current_user.email
        )
        db.session.add(batch)
        db.session.commit()
        flash('Batch added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding batch: {str(e)}', 'error')
    
    return redirect(url_for('batch_management'))

@app.route('/product-codes')
@require_login
def product_codes():
    page = request.args.get('page', 1, type=int)
    codes = ProductCode.query.order_by(ProductCode.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('product_codes.html', codes=codes)

@app.route('/generate-product-codes')
@require_login
def generate_product_codes_page():
    products = Product.query.all()
    batches = Batch.query.all()
    return render_template('generate_product_codes.html', products=products, batches=batches)

@app.route('/generate-codes', methods=['POST'])
@require_login
def generate_codes():
    try:
        product_id = request.form['product_id']
        batch_id = request.form['batch_id']
        quantity = int(request.form['quantity'])
        rejection_percentage = float(request.form.get('rejection_percentage', 0))
        
        # Calculate codes
        total_codes = quantity
        rejected_codes = int(quantity * rejection_percentage / 100)
        mapped_codes = total_codes - rejected_codes
        
        # Get product and batch for QR code generation
        from utils import generate_scannable_qr_data
        product = Product.query.get(product_id)
        batch = Batch.query.get(batch_id)
        
        # Generate structured QR code data with URL for external scanning
        base_url = request.url_root.rstrip('/')
        qr_data = generate_scannable_qr_data(
            "PRODUCT",
            product,
            batch,
            {"total_codes": total_codes, "rejection_percentage": rejection_percentage},
            base_url
        )
        
        product_code = ProductCode(
            product_id=product_id,
            batch_id=batch_id,
            qr_code=qr_data,
            total_codes=total_codes,
            mapped_codes=mapped_codes,
            unmapped_codes=rejected_codes
        )
        
        db.session.add(product_code)
        db.session.commit()
        
        flash(f'Generated {total_codes} product codes successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error generating codes: {str(e)}', 'error')
    
    return redirect(url_for('product_codes'))

@app.route('/first-level-codes')
@require_login
def first_level_codes():
    page = request.args.get('page', 1, type=int)
    codes = FirstLevelCode.query.order_by(FirstLevelCode.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('first_level_codes.html', codes=codes)

@app.route('/generate-first-level')
@require_login
def generate_first_level_page():
    products = Product.query.all()
    batches = Batch.query.all()
    return render_template('generate_first_level.html', products=products, batches=batches)

@app.route('/generate-first-level-codes', methods=['POST'])
@require_login
def generate_first_level_codes():
    try:
        product_id = request.form['product_id']
        batch_id = request.form['batch_id']
        quantity = int(request.form['quantity'])
        
        # Get product and batch for QR code generation
        from utils import generate_scannable_qr_data
        product = Product.query.get(product_id)
        batch = Batch.query.get(batch_id)
        
        # Generate structured QR code data with URL for external scanning
        base_url = request.url_root.rstrip('/')
        qr_data = generate_scannable_qr_data(
            "FIRST_LEVEL",
            product,
            batch,
            {"quantity": quantity},
            base_url
        )
        
        first_level_code = FirstLevelCode(
            product_id=product_id,
            batch_id=batch_id,
            qr_code=qr_data,
            total_codes=quantity,
            mapped_codes=quantity,
            unmapped_codes=0
        )
        
        db.session.add(first_level_code)
        db.session.commit()
        
        flash(f'Generated {quantity} first level codes successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error generating first level codes: {str(e)}', 'error')
    
    return redirect(url_for('first_level_codes'))

@app.route('/second-level-codes')
@require_login
def second_level_codes():
    page = request.args.get('page', 1, type=int)
    codes = SecondLevelCode.query.order_by(SecondLevelCode.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('second_level_codes.html', codes=codes)

@app.route('/generate-second-level')
@require_login
def generate_second_level_page():
    products = Product.query.all()
    batches = Batch.query.all()
    return render_template('generate_second_level.html', products=products, batches=batches)

@app.route('/generate-second-level-codes', methods=['POST'])
@require_login
def generate_second_level_codes():
    try:
        product_id = request.form['product_id']
        batch_id = request.form['batch_id']
        quantity = int(request.form['quantity'])
        
        # Get product and batch for QR code generation
        from utils import generate_scannable_qr_data
        product = Product.query.get(product_id)
        batch = Batch.query.get(batch_id)
        
        # Generate structured QR code data with URL for external scanning
        base_url = request.url_root.rstrip('/')
        qr_data = generate_scannable_qr_data(
            "SECOND_LEVEL",
            product,
            batch,
            {"quantity": quantity},
            base_url
        )
        
        second_level_code = SecondLevelCode(
            product_id=product_id,
            batch_id=batch_id,
            qr_code=qr_data,
            quantity=quantity
        )
        
        db.session.add(second_level_code)
        db.session.commit()
        
        flash(f'Generated {quantity} second level codes successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error generating second level codes: {str(e)}', 'error')
    
    return redirect(url_for('second_level_codes'))

@app.route('/shipper-codes')
@require_login
def shipper_codes():
    page = request.args.get('page', 1, type=int)
    codes = ShipperCode.query.order_by(ShipperCode.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('shipper_codes.html', codes=codes)

@app.route('/create-shipper')
@require_login
def create_shipper():
    products = Product.query.order_by(Product.name).all()
    return render_template('create_shipper.html', products=products)

@app.route('/shipper-details/<int:shipper_id>')
@require_login
def shipper_details(shipper_id):
    shipper = ShipperCode.query.get_or_404(shipper_id)
    return render_template('shipper_details.html', shipper=shipper)

@app.route('/generate-shipper-codes', methods=['POST'])
@require_login
def generate_shipper_codes():
    try:
        import uuid
        from datetime import datetime
        
        # Get form data
        shipper_name = request.form.get('shipper_name', '')
        selected_products = request.form.getlist('selected_products[]')  # List of product IDs
        selected_quantities = request.form.getlist('selected_quantities[]')  # Corresponding quantities
        gross_weight = float(request.form.get('gross_weight', 0))
        
        if not selected_products:
            flash('Please select at least one product for the shipper', 'error')
            return redirect(url_for('shipper_codes'))
        
        # Generate unique shipper code
        shipper_code_value = f"SHIP{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        
        # Calculate totals
        total_products = len(selected_products)
        total_quantity = sum(int(qty) for qty in selected_quantities)
        
        # Create all product details for QR code
        products_details = []
        for i, product_id in enumerate(selected_products):
            product = Product.query.get(product_id)
            quantity = int(selected_quantities[i])
            
            if product:
                products_details.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'sku_id': product.sku_id,
                    'gtin': product.gtin,
                    'quantity': quantity,
                    'mfg_date': product.batches[0].mfg_date.isoformat() if product.batches else None,
                    'expiry_date': product.batches[0].expiry_date.isoformat() if product.batches else None
                })
        
        # Generate comprehensive QR code data with all product details
        import json
        base_url = request.url_root.rstrip('/')
        qr_data_dict = {
            'type': 'SHIPPER',
            'shipper_code': shipper_code_value,
            'shipper_name': shipper_name,
            'total_products': total_products,
            'total_quantity': total_quantity,
            'gross_weight': gross_weight,
            'products': products_details,
            'timestamp': datetime.now().isoformat(),
            'scan_url': f"{base_url}/scan"
        }
        
        # Create QR data with fallback for different environments
        qr_data = json.dumps(qr_data_dict)
        scan_url = f"{base_url}/scan?data={qr_data}"
        final_qr_data = f"{scan_url}#{qr_data}"  # URL with fallback data in fragment
        
        # Create shipper code record
        shipper = ShipperCode(
            shipper_code=shipper_code_value,
            shipper_name=shipper_name,
            total_products=total_products,
            total_quantity=total_quantity,
            gross_weight=gross_weight,
            qr_code=final_qr_data
        )
        
        db.session.add(shipper)
        db.session.flush()  # Get the ID before adding products
        
        # Add all products to the shipper
        for i, product_id in enumerate(selected_products):
            quantity = int(selected_quantities[i])
            
            # Get the most recent batch for this product (or handle batch selection)
            product = Product.query.get(product_id)
            batch = product.batches[0] if product.batches else None
            
            shipper_product = ShipperProduct(
                shipper_code_id=shipper.id,
                product_id=product_id,
                batch_id=batch.id if batch else None,
                quantity=quantity
            )
            db.session.add(shipper_product)
        
        db.session.commit()
        
        flash(f'Generated shipper "{shipper_code_value}" with {total_products} products successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error generating shipper codes: {str(e)}', 'error')
        print(f"Shipper generation error: {e}")  # For debugging
    
    return redirect(url_for('shipper_codes'))

@app.route('/stock-report')
@require_login
def stock_report():
    page = request.args.get('page', 1, type=int)
    
    # Get factories with stock information
    factories = Factory.query.order_by(Factory.name).paginate(
        page=page, per_page=10, error_out=False)
    
    # Calculate stock totals for each factory
    for factory in factories.items:
        total_stock = db.session.query(db.func.sum(Stock.units)).filter_by(factory_id=factory.id).scalar() or 0
        factory.total_stock = total_stock
    
    # Calculate overall statistics
    total_stock = db.session.query(db.func.sum(Stock.units)).filter_by(bin_status='OK').scalar() or 0
    transit_stock = db.session.query(db.func.sum(Stock.units)).filter_by(bin_status='intransit').scalar() or 0
    total_products = Product.query.count()
    
    return render_template('stock_report.html', 
                         factories=factories,
                         total_stock=total_stock,
                         transit_stock=transit_stock,
                         total_products=total_products)

@app.route('/stock-detail/<factory_id>')
@require_login
def stock_detail(factory_id):
    page = request.args.get('page', 1, type=int)
    factory = Factory.query.get_or_404(factory_id)
    
    stock_items = Stock.query.filter_by(factory_id=factory_id).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('stock_detail.html', factory=factory, stock_items=stock_items)

@app.route('/batch-detail/<product_id>')
@require_login
def batch_detail(product_id):
    page = request.args.get('page', 1, type=int)
    product = Product.query.get_or_404(product_id)
    
    batches = Batch.query.filter_by(product_id=product_id).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('batch_detail.html', product=product, batches=batches)

@app.route('/export-codes/<int:code_id>')
@require_login
def export_codes(code_id):
    code = ProductCode.query.get_or_404(code_id)
    
    data = [
        [code.product.name, code.product.sku_id, code.batch.batch_no, 
         code.total_codes, code.mapped_codes, code.unmapped_codes]
    ]
    
    headers = ['Product Name', 'SKU ID', 'Batch No', 'Total Codes', 'Mapped Codes', 'Unmapped Codes']
    
    return export_to_excel(data, f'product_codes_{code_id}.xlsx', headers)

@app.route('/export-batch-stock/<batch_id>')
@require_login
def export_batch_stock(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    stock_items = Stock.query.filter_by(batch_id=batch_id).all()
    
    data = []
    for stock in stock_items:
        data.append([
            batch.batch_no,
            stock.product.name if stock.product else 'N/A',
            stock.product.sku_id if stock.product else 'N/A',
            stock.units,
            stock.bin_status,
            stock.factory.name if stock.factory else 'N/A',
            batch.mfg_date.strftime('%d-%m-%Y'),
            batch.expiry_date.strftime('%d-%m-%Y'),
            batch.qa_status
        ])
    
    headers = ['Batch No', 'Product Name', 'SKU ID', 'Units', 'Bin Status', 'Factory', 'Mfg Date', 'Expiry Date', 'QA Status']
    
    return export_to_excel(data, f'batch_stock_{batch_id}.xlsx', headers)

@app.route('/export-all-batches')
@require_login
def export_all_batches():
    batches = Batch.query.join(Product).join(Factory).all()
    
    data = []
    for batch in batches:
        stock_total = db.session.query(db.func.sum(Stock.units)).filter_by(batch_id=batch.id).scalar() or 0
        data.append([
            batch.batch_no,
            batch.product.name if batch.product else 'N/A',
            batch.product.sku_id if batch.product else 'N/A',
            batch.factory.name if batch.factory else 'N/A',
            stock_total,
            batch.mfg_date.strftime('%d-%m-%Y'),
            batch.expiry_date.strftime('%d-%m-%Y'),
            batch.qa_status,
            batch.created_at.strftime('%d-%m-%Y %H:%M')
        ])
    
    headers = ['Batch No', 'Product Name', 'SKU ID', 'Factory', 'Total Stock', 'Mfg Date', 'Expiry Date', 'QA Status', 'Created On']
    
    return export_to_excel(data, f'all_batches_{datetime.now().strftime("%Y%m%d")}.xlsx', headers)

@app.route('/export-factory-stock/<factory_id>')
@require_login
def export_factory_stock(factory_id):
    factory = Factory.query.get_or_404(factory_id)
    stock_items = Stock.query.filter_by(factory_id=factory_id).join(Product).join(Batch).all()
    
    data = []
    for stock in stock_items:
        data.append([
            stock.product.name if stock.product else 'N/A',
            stock.product.sku_id if stock.product else 'N/A',
            stock.batch.batch_no if stock.batch else 'N/A',
            stock.units,
            stock.bin_status,
            stock.batch.mfg_date.strftime('%d-%m-%Y') if stock.batch else 'N/A',
            stock.batch.expiry_date.strftime('%d-%m-%Y') if stock.batch else 'N/A',
            stock.updated_at.strftime('%d-%m-%Y %H:%M')
        ])
    
    headers = ['Product Name', 'SKU ID', 'Batch No', 'Units', 'Bin Status', 'Mfg Date', 'Expiry Date', 'Updated']
    
    return export_to_excel(data, f'factory_stock_{factory.name}_{datetime.now().strftime("%Y%m%d")}.xlsx', headers)

@app.route('/export-all-stock')
@require_login
def export_all_stock():
    stock_items = Stock.query.join(Product).join(Batch).join(Factory).all()
    
    data = []
    for stock in stock_items:
        data.append([
            stock.factory.name if stock.factory else 'N/A',
            stock.product.name if stock.product else 'N/A',
            stock.product.sku_id if stock.product else 'N/A',
            stock.batch.batch_no if stock.batch else 'N/A',
            stock.units,
            stock.bin_status,
            stock.batch.mfg_date.strftime('%d-%m-%Y') if stock.batch else 'N/A',
            stock.batch.expiry_date.strftime('%d-%m-%Y') if stock.batch else 'N/A',
            stock.updated_at.strftime('%d-%m-%Y %H:%M')
        ])
    
    headers = ['Factory', 'Product Name', 'SKU ID', 'Batch No', 'Units', 'Bin Status', 'Mfg Date', 'Expiry Date', 'Updated']
    
    return export_to_excel(data, f'all_stock_{datetime.now().strftime("%Y%m%d")}.xlsx', headers)

@app.route('/add-product', methods=['POST'])
@require_login
def add_product():
    try:
        product_id = generate_product_id()
        
        # Handle image upload
        image_url = None
        if 'product_image' in request.files:
            from utils import save_uploaded_image
            image_file = request.files['product_image']
            image_url = save_uploaded_image(image_file, product_id)
        
        product = Product(
            id=product_id,
            name=request.form['name'],
            sku_id=request.form['sku_id'],
            gtin=request.form.get('gtin'),
            mrp=float(request.form['mrp']) if request.form.get('mrp') else None,
            registration_no=request.form.get('registration_no'),
            sap_description=request.form.get('sap_description'),
            image_url=image_url
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding product: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/add-factory', methods=['POST'])
@require_login
def add_factory():
    try:
        factory_id = generate_factory_id()
        factory = Factory(
            id=factory_id,
            name=request.form['name'],
            mobile_no=request.form.get('mobile_no'),
            city=request.form.get('city'),
            state=request.form.get('state')
        )
        db.session.add(factory)
        db.session.commit()
        flash('Factory added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding factory: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

# QR Code display routes
@app.route('/show-qr/<code_type>/<int:code_id>')
@require_login
def show_qr_code(code_type, code_id):
    from utils import generate_qr_code
    
    if code_type == 'product':
        code = ProductCode.query.get_or_404(code_id)
    elif code_type == 'first_level':
        code = FirstLevelCode.query.get_or_404(code_id)
    elif code_type == 'second_level':
        code = SecondLevelCode.query.get_or_404(code_id)
    elif code_type == 'shipper':
        code = ShipperCode.query.get_or_404(code_id)
    else:
        flash('Invalid code type', 'error')
        return redirect(url_for('dashboard'))
    
    qr_image = generate_qr_code(code.qr_code)
    
    return jsonify({
        'qr_image': qr_image,
        'qr_data': code.qr_code
    })

# QR Code Scanner Page
@app.route('/scan')
def scan_qr():
    # Check if data is provided as URL parameter (for external scanners)
    qr_data = request.args.get('data')
    if qr_data:
        from urllib.parse import unquote
        import json
        try:
            decoded_data = unquote(qr_data)
            # Try to parse as JSON to validate
            parsed_data = json.loads(decoded_data)
            return render_template('scan_qr.html', qr_data=decoded_data, parsed_data=parsed_data)
        except json.JSONDecodeError:
            flash('Invalid QR code data format', 'error')
            return render_template('scan_qr.html')
    return render_template('scan_qr.html')

# Public QR Code Scanner (for external scanning) - legacy support
@app.route('/scan/<path:qr_data>')
def scan_qr_with_data(qr_data):
    from urllib.parse import unquote
    import json
    try:
        decoded_data = unquote(qr_data)
        parsed_data = json.loads(decoded_data)
        return render_template('scan_qr.html', qr_data=decoded_data, parsed_data=parsed_data)
    except json.JSONDecodeError:
        flash('Invalid QR code data format', 'error')
        return render_template('scan_qr.html')

# API endpoint for QR code validation and parsing
@app.route('/api/parse-qr', methods=['POST'])
def parse_qr_code():
    """API endpoint to parse QR code data and return product information"""
    import json
    try:
        qr_text = request.json.get('qr_data', '').strip()
        
        # Handle different QR code formats
        if qr_text.startswith('http'):
            # Extract data from URL
            if '/scan?data=' in qr_text:
                from urllib.parse import unquote, urlparse, parse_qs
                parsed_url = urlparse(qr_text)
                qr_data = parse_qs(parsed_url.query).get('data', [''])[0]
                qr_text = unquote(qr_data)
        
        # Parse JSON data
        try:
            qr_data = json.loads(qr_text)
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid QR code format'}), 400
        
        # Validate required fields and code type
        required_fields = ['type', 'product_id', 'batch_id']
        if not all(field in qr_data for field in required_fields):
            return jsonify({'error': 'QR code missing required product information'}), 400
            
        # Get the correct code based on type
        code_type = qr_data.get('type')
        if code_type == 'FIRST_LEVEL':
            code = FirstLevelCode.query.filter_by(qr_code=qr_text).first()
        elif code_type == 'SECOND_LEVEL':
            code = SecondLevelCode.query.filter_by(qr_code=qr_text).first()
        else:
            return jsonify({'error': 'Invalid code type'}), 400
            
        if not code:
            return jsonify({'error': 'Code not found in database'}), 404
            
        # Get additional product and batch info
        product = Product.query.get(qr_data['product_id'])
        batch = Batch.query.get(qr_data['batch_id'])
        
        if not product or not batch:
            return jsonify({'error': 'Product or batch not found'}), 404
            
        return jsonify(qr_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoints for dynamic data
@app.route('/api/batches/<product_id>')
@require_login
def get_batches_by_product(product_id):
    batches = Batch.query.filter_by(product_id=product_id).all()
    return jsonify([{
        'id': batch.id,
        'batch_no': batch.batch_no,
        'mfg_date': batch.mfg_date.strftime('%Y-%m-%d'),
        'expiry_date': batch.expiry_date.strftime('%Y-%m-%d')
    } for batch in batches])

@app.route('/api/products')
@require_login
def get_products():
    products = Product.query.all()
    return jsonify([{
        'id': product.id,
        'name': product.name,
        'sku_id': product.sku_id
    } for product in products])
