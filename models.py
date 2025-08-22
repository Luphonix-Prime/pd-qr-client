from datetime import datetime
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    role = db.Column(db.String(20), default='user')  # user, admin
    factory_id = db.Column(db.String, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def check_password(self, password):
        """Check if provided password matches user's password hash"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """Set password hash from plain password"""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.email.split('@')[0]

# Factory/Location model
class Factory(db.Model):
    __tablename__ = 'factories'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    mobile_no = db.Column(db.String(20), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

# Product model
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sku_id = db.Column(db.String(100), unique=True, nullable=False)
    gtin = db.Column(db.String(50), nullable=True)
    mrp = db.Column(db.Float, nullable=True)
    registration_no = db.Column(db.String(100), nullable=True)
    sap_description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

# Batch model
class Batch(db.Model):
    __tablename__ = 'batches'
    id = db.Column(db.String, primary_key=True)
    batch_no = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.String, db.ForeignKey('products.id'), nullable=False)
    factory_id = db.Column(db.String, db.ForeignKey('factories.id'), nullable=False)
    mfg_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    qa_status = db.Column(db.String(20), default='OK')  # OK, Rejected
    responded_by = db.Column(db.String(100), nullable=True)
    responded_date = db.Column(db.DateTime, nullable=True)
    reject_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    product = db.relationship('Product', backref='batches')
    factory = db.relationship('Factory', backref='batches')

# Product QR Codes
class ProductCode(db.Model):
    __tablename__ = 'product_codes'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.String, db.ForeignKey('batches.id'), nullable=False)
    qr_code = db.Column(db.String(500), nullable=False)
    mapped_codes = db.Column(db.Integer, default=0)
    unmapped_codes = db.Column(db.Integer, default=0)
    total_codes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    product = db.relationship('Product', backref='product_codes')
    batch = db.relationship('Batch', backref='product_codes')

# First Level Inner Codes
class FirstLevelCode(db.Model):
    __tablename__ = 'first_level_codes'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.String, db.ForeignKey('batches.id'), nullable=False)
    qr_code = db.Column(db.String(500), nullable=True)
    total_codes = db.Column(db.Integer, default=0)
    mapped_codes = db.Column(db.Integer, default=0)
    unmapped_codes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    product = db.relationship('Product', backref='first_level_codes')
    batch = db.relationship('Batch', backref='first_level_codes')

# Second Level Inner Codes
class SecondLevelCode(db.Model):
    __tablename__ = 'second_level_codes'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.String, db.ForeignKey('batches.id'), nullable=False)
    qr_code = db.Column(db.String(500), nullable=True)
    quantity = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    product = db.relationship('Product', backref='second_level_codes')
    batch = db.relationship('Batch', backref='second_level_codes')

# Shipper Codes - Container for multiple products
class ShipperCode(db.Model):
    __tablename__ = 'shipper_codes'
    id = db.Column(db.Integer, primary_key=True)
    shipper_code = db.Column(db.String(100), unique=True, nullable=False)
    shipper_name = db.Column(db.String(200), nullable=True)  # Custom shipper name
    total_products = db.Column(db.Integer, default=0)  # Total number of products in this shipper
    total_quantity = db.Column(db.Integer, default=0)  # Total quantity in this shipper
    gross_weight = db.Column(db.Float, nullable=True)  # Total weight of shipper
    qr_code = db.Column(db.String(500), nullable=True)  # QR code data with all product details
    qr_code_path = db.Column(db.String(200))  # Path to QR code image
    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(50), default='Active')  # Active, Shipped, Delivered

# Junction table for shipper products (many-to-many relationship)
class ShipperProduct(db.Model):
    __tablename__ = 'shipper_products'
    id = db.Column(db.Integer, primary_key=True)
    shipper_code_id = db.Column(db.Integer, db.ForeignKey('shipper_codes.id'), nullable=False)
    product_id = db.Column(db.String, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.String, db.ForeignKey('batches.id'), nullable=False)
    first_level_code_id = db.Column(db.Integer, db.ForeignKey('first_level_codes.id'), nullable=True)
    second_level_code_id = db.Column(db.Integer, db.ForeignKey('second_level_codes.id'), nullable=True)
    quantity = db.Column(db.Integer, default=1)  # Quantity of this product in the shipper
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    shipper_code = db.relationship('ShipperCode', backref='shipper_products')
    product = db.relationship('Product', backref='in_shipper_products')
    batch = db.relationship('Batch', backref='in_shipper_products')
    first_level_code = db.relationship('FirstLevelCode', backref='in_shipper_products')
    second_level_code = db.relationship('SecondLevelCode', backref='in_shipper_products')

# Stock model for inventory tracking
class Stock(db.Model):
    __tablename__ = 'stock'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.String, db.ForeignKey('batches.id'), nullable=False)
    factory_id = db.Column(db.String, db.ForeignKey('factories.id'), nullable=False)
    units = db.Column(db.Integer, default=0)
    bin_status = db.Column(db.String(20), default='OK')  # OK, intransit
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    product = db.relationship('Product', backref='stock_entries')
    batch = db.relationship('Batch', backref='stock_entries')
    factory = db.relationship('Factory', backref='stock_entries')
