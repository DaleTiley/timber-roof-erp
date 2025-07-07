from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100))  # e.g., "Project Manager", "Director"
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    mobile = db.Column(db.String(20))
    department = db.Column(db.String(100))
    is_primary = db.Column(db.Boolean, default=False)
    is_billing = db.Column(db.Boolean, default=False)
    is_technical = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='Active')  # Active, Inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'title': self.title,
            'email': self.email,
            'phone': self.phone,
            'mobile': self.mobile,
            'department': self.department,
            'is_primary': self.is_primary,
            'is_billing': self.is_billing,
            'is_technical': self.is_technical,
            'notes': self.notes,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'customer_name': self.customer.name if self.customer else None
        }
    
    def __repr__(self):
        return f'<Contact {self.full_name}>'

