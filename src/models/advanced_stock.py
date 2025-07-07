from src.models.user import db
from datetime import datetime, timedelta
from decimal import Decimal
import json

class StockCategory(db.Model):
    __tablename__ = 'stock_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category_type = db.Column(db.String(20), nullable=False)  # STANDARD, MANUFACTURED, SERVICE, COMPOSITE
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stock_items = db.relationship('AdvancedStockItem', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'category_type': self.category_type,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

class VariantAttribute(db.Model):
    __tablename__ = 'variant_attributes'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    attribute_type = db.Column(db.String(20), nullable=False)  # COLOR, DESCRIPTION, GIRTH, FINISH, LENGTH, etc.
    data_type = db.Column(db.String(20), default='TEXT')  # TEXT, NUMBER, DECIMAL, BOOLEAN
    is_required = db.Column(db.Boolean, default=False)
    default_value = db.Column(db.String(200))
    validation_rules = db.Column(db.JSON)  # Store validation rules as JSON
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'attribute_type': self.attribute_type,
            'data_type': self.data_type,
            'is_required': self.is_required,
            'default_value': self.default_value,
            'validation_rules': self.validation_rules,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

class VariantAttributeValue(db.Model):
    __tablename__ = 'variant_attribute_values'
    
    id = db.Column(db.Integer, primary_key=True)
    attribute_id = db.Column(db.Integer, db.ForeignKey('variant_attributes.id'), nullable=False)
    value_code = db.Column(db.String(50), nullable=False)
    value_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attribute = db.relationship('VariantAttribute', backref='values')
    
    def to_dict(self):
        return {
            'id': self.id,
            'attribute_id': self.attribute_id,
            'value_code': self.value_code,
            'value_name': self.value_name,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

class AdvancedStockItem(db.Model):
    __tablename__ = 'advanced_stock_items'
    
    id = db.Column(db.Integer, primary_key=True)
    base_code = db.Column(db.String(50), nullable=False)  # Base code without variants
    full_code = db.Column(db.String(200), unique=True, nullable=False)  # Full code with variants
    description = db.Column(db.String(500), nullable=False)
    long_description = db.Column(db.Text)
    
    # Category and Type
    category_id = db.Column(db.Integer, db.ForeignKey('stock_categories.id'), nullable=False)
    stock_type_id = db.Column(db.Integer, db.ForeignKey('stock_types.id'), nullable=False)
    
    # Parent-Child relationship for variants
    parent_item_id = db.Column(db.Integer, db.ForeignKey('advanced_stock_items.id'))
    is_base_item = db.Column(db.Boolean, default=True)  # True for base items, False for variants
    
    # Units of Measure
    stocked_uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'), nullable=False)
    sales_uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'), nullable=False)
    purchase_uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'), nullable=False)
    
    # UOM Conversions
    sales_to_stock_factor = db.Column(db.Numeric(18, 6), default=1.0)
    purchase_to_stock_factor = db.Column(db.Numeric(18, 6), default=1.0)
    
    # Costing
    standard_cost = db.Column(db.Numeric(18, 4), default=0.0)
    last_cost = db.Column(db.Numeric(18, 4), default=0.0)
    average_cost = db.Column(db.Numeric(18, 4), default=0.0)
    
    # Pricing Groups
    margin_group_id = db.Column(db.Integer, db.ForeignKey('margin_groups.id'))
    discount_group_id = db.Column(db.Integer, db.ForeignKey('discount_groups.id'))
    commission_group_id = db.Column(db.Integer, db.ForeignKey('commission_groups.id'))
    
    # Special Properties for Complex Items
    has_variants = db.Column(db.Boolean, default=False)
    requires_tally = db.Column(db.Boolean, default=False)  # For cut-to-length items
    cover_width = db.Column(db.Numeric(10, 3))  # For sheeting calculations
    default_girth = db.Column(db.Numeric(10, 3))  # For flashings
    coverage_per_unit = db.Column(db.Numeric(18, 6))  # For tiles, etc.
    
    # Variant Attributes (JSON storage for flexibility)
    variant_attributes = db.Column(db.JSON)  # Store variant attribute values
    
    # BOM Information (for manufactured items)
    is_manufactured = db.Column(db.Boolean, default=False)
    has_bom = db.Column(db.Boolean, default=False)
    
    # Service Item Properties
    is_service_item = db.Column(db.Boolean, default=False)
    service_type = db.Column(db.String(50))  # LABOUR, TRANSPORT, CERTIFICATION, etc.
    
    # Composite Rate Properties (for tender rates)
    is_composite_rate = db.Column(db.Boolean, default=False)
    includes_supply = db.Column(db.Boolean, default=True)
    includes_install = db.Column(db.Boolean, default=False)
    
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
    
    # Relationships
    parent_item = db.relationship('AdvancedStockItem', remote_side=[id], backref='variant_items')
    bom_components = db.relationship('BillOfMaterials', foreign_keys='BillOfMaterials.parent_item_id', backref='parent_item')
    bom_usages = db.relationship('BillOfMaterials', foreign_keys='BillOfMaterials.component_item_id', backref='component_item')
    composite_components = db.relationship('CompositeRateComponent', foreign_keys='CompositeRateComponent.composite_item_id', backref='composite_item')
    
    def generate_full_code(self):
        """Generate full code including variant attributes"""
        if not self.variant_attributes or not self.has_variants:
            return self.base_code
        
        code_parts = [self.base_code]
        
        # Add variant attributes to code
        if self.variant_attributes:
            for attr_code, attr_value in self.variant_attributes.items():
                if attr_value:
                    code_parts.append(f"{{{attr_value}}}")
        
        return " ".join(code_parts)
    
    def calculate_selling_price(self, quantity=1.0, length=None):
        """Calculate selling price considering margins, UOM conversions, and special properties"""
        base_cost = float(self.standard_cost or 0.0)
        
        # Apply margin
        margin_percentage = 0.0
        if self.margin_group and self.margin_group.default_margin_percentage:
            margin_percentage = float(self.margin_group.default_margin_percentage)
        
        selling_price = base_cost * (1 + margin_percentage / 100)
        
        # Handle special calculations for different item types
        if self.requires_tally and length:
            # For cut-to-length items (sheeting)
            total_length = quantity * length
            total_price = selling_price * total_length
        elif self.cover_width and self.sales_uom and self.sales_uom.code == 'M2':
            # For sheeting sold by m2 but priced by linear meter
            linear_meters = quantity / (float(self.cover_width) / 1000)  # Convert mm to m
            total_price = selling_price * linear_meters
        elif self.coverage_per_unit:
            # For items like tiles
            units_needed = quantity / float(self.coverage_per_unit)
            total_price = selling_price * units_needed
        else:
            # Standard calculation
            total_price = selling_price * quantity
        
        return total_price
    
    def to_dict(self):
        return {
            'id': self.id,
            'base_code': self.base_code,
            'full_code': self.full_code,
            'description': self.description,
            'long_description': self.long_description,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'category_type': self.category.category_type if self.category else None,
            'stock_type_id': self.stock_type_id,
            'stock_type_name': self.stock_type.name if self.stock_type else None,
            'parent_item_id': self.parent_item_id,
            'is_base_item': self.is_base_item,
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
            'has_variants': self.has_variants,
            'requires_tally': self.requires_tally,
            'cover_width': float(self.cover_width) if self.cover_width else None,
            'default_girth': float(self.default_girth) if self.default_girth else None,
            'coverage_per_unit': float(self.coverage_per_unit) if self.coverage_per_unit else None,
            'variant_attributes': self.variant_attributes,
            'is_manufactured': self.is_manufactured,
            'has_bom': self.has_bom,
            'is_service_item': self.is_service_item,
            'service_type': self.service_type,
            'is_composite_rate': self.is_composite_rate,
            'includes_supply': self.includes_supply,
            'includes_install': self.includes_install,
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

class BillOfMaterials(db.Model):
    __tablename__ = 'bill_of_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    parent_item_id = db.Column(db.Integer, db.ForeignKey('advanced_stock_items.id'), nullable=False)
    component_item_id = db.Column(db.Integer, db.ForeignKey('advanced_stock_items.id'), nullable=False)
    quantity_required = db.Column(db.Numeric(18, 6), nullable=False)
    uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'), nullable=False)
    waste_percentage = db.Column(db.Numeric(5, 2), default=0.0)
    is_optional = db.Column(db.Boolean, default=False)
    sequence_number = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uom = db.relationship('UnitOfMeasure', backref='bom_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'parent_item_id': self.parent_item_id,
            'parent_item_code': self.parent_item.full_code if self.parent_item else None,
            'component_item_id': self.component_item_id,
            'component_item_code': self.component_item.full_code if self.component_item else None,
            'component_item_description': self.component_item.description if self.component_item else None,
            'quantity_required': float(self.quantity_required),
            'uom_id': self.uom_id,
            'uom_code': self.uom.code if self.uom else None,
            'waste_percentage': float(self.waste_percentage) if self.waste_percentage else 0.0,
            'is_optional': self.is_optional,
            'sequence_number': self.sequence_number,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

class CompositeRateComponent(db.Model):
    __tablename__ = 'composite_rate_components'
    
    id = db.Column(db.Integer, primary_key=True)
    composite_item_id = db.Column(db.Integer, db.ForeignKey('advanced_stock_items.id'), nullable=False)
    component_item_id = db.Column(db.Integer, db.ForeignKey('advanced_stock_items.id'), nullable=False)
    quantity_required = db.Column(db.Numeric(18, 6), nullable=False)
    uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'), nullable=False)
    component_type = db.Column(db.String(20), nullable=False)  # MATERIAL, LABOUR, TRANSPORT, OTHER
    is_included_in_supply = db.Column(db.Boolean, default=True)
    is_included_in_install = db.Column(db.Boolean, default=False)
    sequence_number = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uom = db.relationship('UnitOfMeasure', backref='composite_components')
    component_item = db.relationship('AdvancedStockItem', foreign_keys=[component_item_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'composite_item_id': self.composite_item_id,
            'composite_item_code': self.composite_item.full_code if self.composite_item else None,
            'component_item_id': self.component_item_id,
            'component_item_code': self.component_item.full_code if self.component_item else None,
            'component_item_description': self.component_item.description if self.component_item else None,
            'quantity_required': float(self.quantity_required),
            'uom_id': self.uom_id,
            'uom_code': self.uom.code if self.uom else None,
            'component_type': self.component_type,
            'is_included_in_supply': self.is_included_in_supply,
            'is_included_in_install': self.is_included_in_install,
            'sequence_number': self.sequence_number,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

class TemporaryStockItem(db.Model):
    __tablename__ = 'temporary_stock_items'
    
    id = db.Column(db.Integer, primary_key=True)
    temp_code = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    long_description = db.Column(db.Text)
    
    # Basic properties
    estimated_cost = db.Column(db.Numeric(18, 4), default=0.0)
    sales_uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'), nullable=False)
    
    # Expiration
    expiry_date = db.Column(db.DateTime, nullable=False)
    is_expired = db.Column(db.Boolean, default=False)
    
    # Conversion tracking
    converted_to_permanent = db.Column(db.Boolean, default=False)
    permanent_item_id = db.Column(db.Integer, db.ForeignKey('advanced_stock_items.id'))
    
    # Usage tracking
    times_used = db.Column(db.Integer, default=0)
    last_used_date = db.Column(db.DateTime)
    
    # Audit
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    # Relationships
    sales_uom = db.relationship('UnitOfMeasure', backref='temp_stock_items')
    permanent_item = db.relationship('AdvancedStockItem', backref='temp_origins')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.expiry_date:
            self.expiry_date = datetime.utcnow() + timedelta(days=120)
    
    def is_expired_now(self):
        return datetime.utcnow() > self.expiry_date
    
    def extend_expiry(self, days=120):
        self.expiry_date = datetime.utcnow() + timedelta(days=days)
    
    def to_dict(self):
        return {
            'id': self.id,
            'temp_code': self.temp_code,
            'description': self.description,
            'long_description': self.long_description,
            'estimated_cost': float(self.estimated_cost) if self.estimated_cost else 0.0,
            'sales_uom_id': self.sales_uom_id,
            'sales_uom_code': self.sales_uom.code if self.sales_uom else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'is_expired': self.is_expired or self.is_expired_now(),
            'converted_to_permanent': self.converted_to_permanent,
            'permanent_item_id': self.permanent_item_id,
            'permanent_item_code': self.permanent_item.full_code if self.permanent_item else None,
            'times_used': self.times_used,
            'last_used_date': self.last_used_date.isoformat() if self.last_used_date else None,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'created_by': self.created_by,
            'notes': self.notes
        }

