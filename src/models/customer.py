from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from decimal import Decimal
from src.models.user import db

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    company_type = db.Column(db.String(100))  # e.g., "Commercial Builder", "Roofing Contractor"
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    province = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100), default='South Africa')
    vat_number = db.Column(db.String(50))
    registration_number = db.Column(db.String(50))
    credit_limit = db.Column(db.Numeric(15, 2), default=0.00)
    payment_terms = db.Column(db.Integer, default=30)  # Days
    discount_group_id = db.Column(db.Integer)  # Foreign key to discount groups
    margin_group_id = db.Column(db.Integer)   # Foreign key to margin groups
    status = db.Column(db.String(20), default='Active')  # Active, Inactive, Suspended
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to contacts
    contacts = db.relationship('Contact', backref='customer', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'company_type': self.company_type,
            'email': self.email,
            'phone': self.phone,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'city': self.city,
            'province': self.province,
            'postal_code': self.postal_code,
            'country': self.country,
            'vat_number': self.vat_number,
            'registration_number': self.registration_number,
            'credit_limit': float(self.credit_limit) if self.credit_limit else 0.0,
            'payment_terms': self.payment_terms,
            'discount_group_id': self.discount_group_id,
            'margin_group_id': self.margin_group_id,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'contacts_count': len(self.contacts) if self.contacts else 0
        }
    
    def __repr__(self):
        return f'<Customer {self.name}>'

