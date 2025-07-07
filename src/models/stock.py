from src.models.user import db
from datetime import datetime
from decimal import Decimal

class StockType(db.Model):
    __tablename__ = 'stock_types'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    properties = db.Column(db.JSON)  # Store type-specific properties
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock_items = db.relationship('StockItem', backref='stock_type', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'properties': self.properties,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None
        }

class UnitOfMeasure(db.Model):
    __tablename__ = 'units_of_measure'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    unit_type = db.Column(db.String(20))  # length, weight, area, volume, count, etc.
    base_unit_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'))
    conversion_factor = db.Column(db.Numeric(18, 6), default=1.0)  # Factor to convert to base unit
    is_base_unit = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referential relationship for base unit
    base_unit = db.relationship('UnitOfMeasure', remote_side=[id], backref='derived_units')
    
    # Relationships
    stock_items_stocked = db.relationship('StockItem', foreign_keys='StockItem.stocked_uom_id', backref='stocked_uom', lazy=True)
    stock_items_sales = db.relationship('StockItem', foreign_keys='StockItem.sales_uom_id', backref='sales_uom', lazy=True)
    stock_items_purchase = db.relationship('StockItem', foreign_keys='StockItem.purchase_uom_id', backref='purchase_uom', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'unit_type': self.unit_type,
            'base_unit_id': self.base_unit_id,
            'base_unit_name': self.base_unit.name if self.base_unit else None,
            'conversion_factor': float(self.conversion_factor) if self.conversion_factor else 1.0,
            'is_base_unit': self.is_base_unit,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

class MarginGroup(db.Model):
    __tablename__ = 'margin_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    default_margin_percentage = db.Column(db.Numeric(5, 2), default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stock_items = db.relationship('StockItem', backref='margin_group', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'default_margin_percentage': float(self.default_margin_percentage) if self.default_margin_percentage else 0.0,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

class DiscountGroup(db.Model):
    __tablename__ = 'discount_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    default_discount_percentage = db.Column(db.Numeric(5, 2), default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stock_items = db.relationship('StockItem', backref='discount_group', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'default_discount_percentage': float(self.default_discount_percentage) if self.default_discount_percentage else 0.0,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

class CommissionGroup(db.Model):
    __tablename__ = 'commission_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    default_commission_percentage = db.Column(db.Numeric(5, 2), default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stock_items = db.relationship('StockItem', backref='commission_group', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'default_commission_percentage': float(self.default_commission_percentage) if self.default_commission_percentage else 0.0,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

class StockItem(db.Model):
    __tablename__ = 'stock_items'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    long_description = db.Column(db.Text)
    
    # Stock Type
    stock_type_id = db.Column(db.Integer, db.ForeignKey('stock_types.id'), nullable=False)
    
    # Units of Measure
    stocked_uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'), nullable=False)
    sales_uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'), nullable=False)
    purchase_uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'), nullable=False)
    
    # UOM Conversions
    sales_to_stock_factor = db.Column(db.Numeric(18, 6), default=1.0)  # How many stock units = 1 sales unit
    purchase_to_stock_factor = db.Column(db.Numeric(18, 6), default=1.0)  # How many stock units = 1 purchase unit
    
    # Costing
    standard_cost = db.Column(db.Numeric(18, 4), default=0.0)
    last_cost = db.Column(db.Numeric(18, 4), default=0.0)
    average_cost = db.Column(db.Numeric(18, 4), default=0.0)
    
    # Pricing Groups
    margin_group_id = db.Column(db.Integer, db.ForeignKey('margin_groups.id'))
    discount_group_id = db.Column(db.Integer, db.ForeignKey('discount_groups.id'))
    commission_group_id = db.Column(db.Integer, db.ForeignKey('commission_groups.id'))
    
    # Stock Properties (JSON for flexibility)
    properties = db.Column(db.JSON)  # Store item-specific properties like dimensions, grade, etc.
    
    # Stock Control
    track_stock = db.Column(db.Boolean, default=True)
    minimum_stock_level = db.Column(db.Numeric(18, 4), default=0.0)
    maximum_stock_level = db.Column(db.Numeric(18, 4), default=0.0)
    reorder_level = db.Column(db.Numeric(18, 4), default=0.0)
    reorder_quantity = db.Column(db.Numeric(18, 4), default=0.0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_sellable = db.Column(db.Boolean, default=True)
    is_purchasable = db.Column(db.Boolean, default=True)
    
    # Audit
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))
    updated_by = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'description': self.description,
            'long_description': self.long_description,
            'stock_type_id': self.stock_type_id,
            'stock_type_name': self.stock_type.name if self.stock_type else None,
            'stocked_uom_id': self.stocked_uom_id,
            'stocked_uom_code': self.stocked_uom.code if self.stocked_uom else None,
            'sales_uom_id': self.sales_uom_id,
            'sales_uom_code': self.sales_uom.code if self.sales_uom else None,
            'purchase_uom_id': self.purchase_uom_id,
            'purchase_uom_code': self.purchase_uom.code if self.purchase_uom else None,
            'sales_to_stock_factor': float(self.sales_to_stock_factor) if self.sales_to_stock_factor else 1.0,
            'purchase_to_stock_factor': float(self.purchase_to_stock_factor) if self.purchase_to_stock_factor else 1.0,
            'standard_cost': float(self.standard_cost) if self.standard_cost else 0.0,
            'last_cost': float(self.last_cost) if self.last_cost else 0.0,
            'average_cost': float(self.average_cost) if self.average_cost else 0.0,
            'margin_group_id': self.margin_group_id,
            'margin_group_name': self.margin_group.name if self.margin_group else None,
            'discount_group_id': self.discount_group_id,
            'discount_group_name': self.discount_group.name if self.discount_group else None,
            'commission_group_id': self.commission_group_id,
            'commission_group_name': self.commission_group.name if self.commission_group else None,
            'properties': self.properties,
            'track_stock': self.track_stock,
            'minimum_stock_level': float(self.minimum_stock_level) if self.minimum_stock_level else 0.0,
            'maximum_stock_level': float(self.maximum_stock_level) if self.maximum_stock_level else 0.0,
            'reorder_level': float(self.reorder_level) if self.reorder_level else 0.0,
            'reorder_quantity': float(self.reorder_quantity) if self.reorder_quantity else 0.0,
            'is_active': self.is_active,
            'is_sellable': self.is_sellable,
            'is_purchasable': self.is_purchasable,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by
        }

