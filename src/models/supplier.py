from datetime import datetime
from src.models.user import db

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    fax = db.Column(db.String(20))
    website = db.Column(db.String(200))
    
    # Address Information
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    province = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100), default='South Africa')
    
    # Business Information
    registration_number = db.Column(db.String(50))
    vat_number = db.Column(db.String(50))
    tax_number = db.Column(db.String(50))
    
    # Payment Terms
    payment_terms_days = db.Column(db.Integer, default=30)
    credit_limit = db.Column(db.Numeric(15, 2), default=0.0)
    currency = db.Column(db.String(3), default='ZAR')
    
    # Categories and Classification
    supplier_category = db.Column(db.String(50))  # Timber, Steel, Services, etc.
    supplier_type = db.Column(db.String(20), default='VENDOR')  # VENDOR, CONTRACTOR, SERVICE_PROVIDER
    
    # Status and Dates
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, INACTIVE, SUSPENDED, BLACKLISTED
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.String(100))
    approved_date = db.Column(db.DateTime)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notes and Additional Information
    notes = db.Column(db.Text)
    delivery_instructions = db.Column(db.Text)
    quality_rating = db.Column(db.Integer)  # 1-5 rating
    
    # Relationships
    stock_items = db.relationship('StockItem', backref='supplier', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'contact_person': self.contact_person,
            'email': self.email,
            'phone': self.phone,
            'mobile': self.mobile,
            'fax': self.fax,
            'website': self.website,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'city': self.city,
            'province': self.province,
            'postal_code': self.postal_code,
            'country': self.country,
            'registration_number': self.registration_number,
            'vat_number': self.vat_number,
            'tax_number': self.tax_number,
            'payment_terms_days': self.payment_terms_days,
            'credit_limit': float(self.credit_limit) if self.credit_limit else 0.0,
            'currency': self.currency,
            'supplier_category': self.supplier_category,
            'supplier_type': self.supplier_type,
            'status': self.status,
            'is_active': self.is_active,
            'is_approved': self.is_approved,
            'approved_by': self.approved_by,
            'approved_date': self.approved_date.isoformat() if self.approved_date else None,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None,
            'notes': self.notes,
            'delivery_instructions': self.delivery_instructions,
            'quality_rating': self.quality_rating
        }
    
    def __repr__(self):
        return f'<Supplier {self.code}: {self.name}>'

