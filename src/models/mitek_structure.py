from src.models.user import db
from datetime import datetime
from decimal import Decimal
import uuid

class MitekJobStructure(db.Model):
    """Main structure for a Mitek job import"""
    __tablename__ = 'mitek_job_structures'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), nullable=True)
    tender_id = db.Column(db.Integer, db.ForeignKey('tenders.id'), nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    
    mitek_job_number = db.Column(db.String(50), nullable=False)
    job_name = db.Column(db.String(200), nullable=False)
    import_batch_id = db.Column(db.String(50), nullable=False)
    
    # Standard components
    has_trusses = db.Column(db.Boolean, default=True)
    has_infill = db.Column(db.Boolean, default=True)
    has_hangers = db.Column(db.Boolean, default=True)
    
    # Metadata
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)
    imported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='imported')  # imported, processed, quoted
    
    # Relationships
    trusses = db.relationship('MitekTruss', backref='job_structure', lazy=True, cascade='all, delete-orphan')
    infill_items = db.relationship('MitekInfill', backref='job_structure', lazy=True, cascade='all, delete-orphan')
    hangers = db.relationship('MitekHanger', backref='job_structure', lazy=True, cascade='all, delete-orphan')
    sundry_containers = db.relationship('MitekSundryContainer', backref='job_structure', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'quote_id': self.quote_id,
            'mitek_job_number': self.mitek_job_number,
            'job_name': self.job_name,
            'has_trusses': self.has_trusses,
            'has_infill': self.has_infill,
            'has_hangers': self.has_hangers,
            'imported_at': self.imported_at.isoformat() if self.imported_at else None,
            'status': self.status
        }

class MitekTruss(db.Model):
    """Individual truss components"""
    __tablename__ = 'mitek_trusses'
    
    id = db.Column(db.Integer, primary_key=True)
    job_structure_id = db.Column(db.Integer, db.ForeignKey('mitek_job_structures.id'), nullable=False)
    
    truss_mark = db.Column(db.String(20), nullable=False)  # e.g., 3XG1, 4XG2
    truss_type = db.Column(db.String(50), nullable=False)  # e.g., Roof Trusses
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    # Truss specifications
    span = db.Column(db.Numeric(10, 2), nullable=True)
    pitch = db.Column(db.Numeric(5, 2), nullable=True)
    height = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Relationships
    members = db.relationship('MitekTrussMember', backref='truss', lazy=True, cascade='all, delete-orphan')
    plates = db.relationship('MitekTrussPlate', backref='truss', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'truss_mark': self.truss_mark,
            'truss_type': self.truss_type,
            'quantity': self.quantity,
            'span': float(self.span) if self.span else None,
            'pitch': float(self.pitch) if self.pitch else None,
            'height': float(self.height) if self.height else None
        }

class MitekTrussMember(db.Model):
    """Timber members within a truss"""
    __tablename__ = 'mitek_truss_members'
    
    id = db.Column(db.Integer, primary_key=True)
    truss_id = db.Column(db.Integer, db.ForeignKey('mitek_trusses.id'), nullable=False)
    
    member_mark = db.Column(db.String(10), nullable=False)  # e.g., T1, B1, E1, W1
    member_type = db.Column(db.String(20), nullable=False)  # Top, Bottom, End, Web
    timber_size = db.Column(db.String(20), nullable=False)  # e.g., 38x114
    length = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'member_mark': self.member_mark,
            'member_type': self.member_type,
            'timber_size': self.timber_size,
            'length': float(self.length),
            'quantity': self.quantity
        }

class MitekTrussPlate(db.Model):
    """Nail plates for truss connections"""
    __tablename__ = 'mitek_truss_plates'
    
    id = db.Column(db.Integer, primary_key=True)
    truss_id = db.Column(db.Integer, db.ForeignKey('mitek_trusses.id'), nullable=False)
    
    plate_type = db.Column(db.String(20), nullable=False)  # e.g., M20-M8X20
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'plate_type': self.plate_type,
            'quantity': self.quantity
        }

class MitekInfill(db.Model):
    """Infill timber (loose timber without plates)"""
    __tablename__ = 'mitek_infill'
    
    id = db.Column(db.Integer, primary_key=True)
    job_structure_id = db.Column(db.Integer, db.ForeignKey('mitek_job_structures.id'), nullable=False)
    
    infill_mark = db.Column(db.String(20), nullable=False)  # e.g., B1
    timber_size = db.Column(db.String(20), nullable=False)  # e.g., 38x114
    length = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'infill_mark': self.infill_mark,
            'timber_size': self.timber_size,
            'length': float(self.length),
            'quantity': self.quantity
        }

class MitekHanger(db.Model):
    """Hangers and connectors"""
    __tablename__ = 'mitek_hangers'
    
    id = db.Column(db.Integer, primary_key=True)
    job_structure_id = db.Column(db.Integer, db.ForeignKey('mitek_job_structures.id'), nullable=False)
    
    hanger_type = db.Column(db.String(50), nullable=False)  # e.g., ETH38x1MP, UNAIL1
    description = db.Column(db.String(200), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'hanger_type': self.hanger_type,
            'description': self.description,
            'quantity': self.quantity
        }

class MitekSundryContainer(db.Model):
    """Container for imported sundries (like Bracing, Corrugated 762 Only, etc.)"""
    __tablename__ = 'mitek_sundry_containers'
    
    id = db.Column(db.Integer, primary_key=True)
    job_structure_id = db.Column(db.Integer, db.ForeignKey('mitek_job_structures.id'), nullable=False)
    
    container_name = db.Column(db.String(100), nullable=False)  # e.g., "Bracing", "Corrugated 762 Only"
    container_type = db.Column(db.String(50), nullable=False)  # e.g., "bracing", "sheeting", "labour"
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    items = db.relationship('MitekSundryItem', backref='container', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'container_name': self.container_name,
            'container_type': self.container_type,
            'is_active': self.is_active,
            'items_count': len(self.items)
        }

class MitekSundryItem(db.Model):
    """Individual items within sundry containers"""
    __tablename__ = 'mitek_sundry_items'
    
    id = db.Column(db.Integer, primary_key=True)
    container_id = db.Column(db.Integer, db.ForeignKey('mitek_sundry_containers.id'), nullable=False)
    
    item_code = db.Column(db.String(50), nullable=False)
    item_description = db.Column(db.String(200), nullable=False)
    item_category = db.Column(db.String(50), nullable=True)  # e.g., "timber", "nails", "flashing"
    
    # Calculated quantities (from formulas)
    calculated_quantity = db.Column(db.Numeric(15, 4), nullable=False, default=0)
    calculated_unit = db.Column(db.String(10), nullable=False, default='ea')
    
    # Formula information
    formula_id = db.Column(db.Integer, db.ForeignKey('formulas.id'), nullable=True)
    formula_result = db.Column(db.Text, nullable=True)  # JSON of formula calculation details
    
    # Stock linking
    stock_item_id = db.Column(db.Integer, db.ForeignKey('stock_items.id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_code': self.item_code,
            'item_description': self.item_description,
            'item_category': self.item_category,
            'calculated_quantity': float(self.calculated_quantity),
            'calculated_unit': self.calculated_unit,
            'formula_id': self.formula_id,
            'stock_item_id': self.stock_item_id
        }

class NailAggregation(db.Model):
    """Aggregates all nail quantities across different components"""
    __tablename__ = 'nail_aggregations'
    
    id = db.Column(db.Integer, primary_key=True)
    job_structure_id = db.Column(db.Integer, db.ForeignKey('mitek_job_structures.id'), nullable=False)
    
    nail_type = db.Column(db.String(50), nullable=False)  # e.g., "75mm Galv Nails"
    nail_size = db.Column(db.String(20), nullable=False)  # e.g., "75x3.15"
    
    # Aggregated quantities
    total_quantity_ea = db.Column(db.Integer, nullable=False, default=0)  # Total in pieces
    total_quantity_kg = db.Column(db.Numeric(10, 3), nullable=False, default=0)  # Converted to kg
    
    # Conversion factor
    pieces_per_kg = db.Column(db.Integer, nullable=False, default=1)
    
    # Source tracking
    source_components = db.Column(db.Text, nullable=True)  # JSON array of source components
    
    def to_dict(self):
        return {
            'id': self.id,
            'nail_type': self.nail_type,
            'nail_size': self.nail_size,
            'total_quantity_ea': self.total_quantity_ea,
            'total_quantity_kg': float(self.total_quantity_kg),
            'pieces_per_kg': self.pieces_per_kg
        }

class QuoteLineItem(db.Model):
    """Enhanced quote line items that can reference Mitek components"""
    __tablename__ = 'quote_line_items'
    
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), nullable=False)
    
    line_number = db.Column(db.Integer, nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # stock, mitek_truss, mitek_infill, mitek_hanger, mitek_sundry, composite
    
    # Stock item reference
    stock_item_id = db.Column(db.Integer, db.ForeignKey('stock_items.id'), nullable=True)
    
    # Mitek component references
    mitek_truss_id = db.Column(db.Integer, db.ForeignKey('mitek_trusses.id'), nullable=True)
    mitek_infill_id = db.Column(db.Integer, db.ForeignKey('mitek_infill.id'), nullable=True)
    mitek_hanger_id = db.Column(db.Integer, db.ForeignKey('mitek_hangers.id'), nullable=True)
    mitek_sundry_item_id = db.Column(db.Integer, db.ForeignKey('mitek_sundry_items.id'), nullable=True)
    nail_aggregation_id = db.Column(db.Integer, db.ForeignKey('nail_aggregations.id'), nullable=True)
    
    # Composite item reference
    composite_item_id = db.Column(db.Integer, db.ForeignKey('composite_items.id'), nullable=True)
    
    # Line item details
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Numeric(15, 4), nullable=False)
    unit = db.Column(db.String(10), nullable=False)
    unit_price = db.Column(db.Numeric(15, 4), nullable=False)
    line_total = db.Column(db.Numeric(15, 4), nullable=False)
    
    # Pricing details
    cost_price = db.Column(db.Numeric(15, 4), nullable=True)
    margin_percentage = db.Column(db.Numeric(5, 2), nullable=True)
    discount_percentage = db.Column(db.Numeric(5, 2), nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'line_number': self.line_number,
            'item_type': self.item_type,
            'description': self.description,
            'quantity': float(self.quantity),
            'unit': self.unit,
            'unit_price': float(self.unit_price),
            'line_total': float(self.line_total),
            'margin_percentage': float(self.margin_percentage) if self.margin_percentage else None,
            'discount_percentage': float(self.discount_percentage) if self.discount_percentage else None
        }

