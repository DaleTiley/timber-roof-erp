from src.models.user import db
from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid

class ProjectType(Enum):
    HOME_OWNER = "home_owner"
    CONTRACTOR = "contractor"
    DEVELOPER = "developer"

class ProjectStatus(Enum):
    ENQUIRY = "enquiry"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class QuoteStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class TenderStatus(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    AWARDED = "awarded"
    LOST = "lost"
    EXPIRED = "expired"

class OrderStatus(Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    IN_PRODUCTION = "in_production"
    READY_FOR_DELIVERY = "ready_for_delivery"
    DELIVERED = "delivered"
    INSTALLED = "installed"
    COMPLETED = "completed"

# Main Project File (Parent Record)
class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    project_number = db.Column(db.String(15), unique=True, nullable=False)  # E25-1-001
    project_name = db.Column(db.String(200), nullable=False)
    project_type = db.Column(db.Enum(ProjectType), nullable=False)
    status = db.Column(db.Enum(ProjectStatus), default=ProjectStatus.ENQUIRY)
    
    # Customer Information
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    primary_contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    
    # Project Details
    description = db.Column(db.Text)
    site_address = db.Column(db.Text)
    site_city = db.Column(db.String(100))
    site_province = db.Column(db.String(50))
    site_postal_code = db.Column(db.String(10))
    
    # Sales Information
    sales_person_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    estimator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    project_manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Financial Information
    estimated_value = db.Column(db.Numeric(15, 2))
    probability = db.Column(db.Integer, default=50)  # Percentage
    
    # Dates
    enquiry_date = db.Column(db.DateTime, default=datetime.utcnow)
    required_date = db.Column(db.DateTime)
    quote_due_date = db.Column(db.DateTime)
    
    # Document Management
    documents_uploaded = db.Column(db.Boolean, default=False)
    plans_received = db.Column(db.Boolean, default=False)
    site_visit_required = db.Column(db.Boolean, default=False)
    
    # Audit Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    customer = db.relationship('Customer', backref='projects')
    primary_contact = db.relationship('Contact', backref='primary_projects')
    sales_person = db.relationship('User', foreign_keys=[sales_person_id], backref='sales_projects')
    estimator = db.relationship('User', foreign_keys=[estimator_id], backref='estimated_projects')
    project_manager = db.relationship('User', foreign_keys=[project_manager_id], backref='managed_projects')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_projects')
    
    # Child Records
    buildings = db.relationship('ProjectBuilding', backref='project', cascade='all, delete-orphan')
    quotes = db.relationship('Quote', backref='project', cascade='all, delete-orphan')
    tenders = db.relationship('Tender', backref='project', cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='project', cascade='all, delete-orphan')
    documents = db.relationship('ProjectDocument', backref='project', cascade='all, delete-orphan')
    variables = db.relationship('ProjectVariable', backref='project', cascade='all, delete-orphan')

    def generate_project_number(self):
        """Generate project number in format E25-1-001"""
        year = datetime.now().year % 100  # Last 2 digits of year
        
        # Get the next sequence number for this year
        last_project = Project.query.filter(
            Project.project_number.like(f'E{year}-%')
        ).order_by(Project.project_number.desc()).first()
        
        if last_project:
            # Extract sequence from last project number
            parts = last_project.project_number.split('-')
            if len(parts) >= 3:
                sequence = int(parts[2]) + 1
            else:
                sequence = 1
        else:
            sequence = 1
            
        return f'E{year}-1-{sequence:03d}'

    def get_total_pipeline_value(self):
        """Calculate total pipeline value from all quotes"""
        total = 0
        for quote in self.quotes:
            if quote.status in [QuoteStatus.PENDING, QuoteStatus.APPROVED]:
                total += quote.total_value or 0
        return total

# Project Buildings (for tracking multiple buildings/sections)
class ProjectBuilding(db.Model):
    __tablename__ = 'project_buildings'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    building_number = db.Column(db.String(10), nullable=False)  # A, B, C or 1, 2, 3
    building_name = db.Column(db.String(100))
    building_type = db.Column(db.String(100))  # House Type A, Warehouse, etc.
    quantity = db.Column(db.Integer, default=1)
    
    # Building Details
    description = db.Column(db.Text)
    floor_area = db.Column(db.Numeric(10, 2))
    roof_area = db.Column(db.Numeric(10, 2))
    
    # Status
    status = db.Column(db.String(50), default='Active')
    
    # Audit Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Quote Management
class Quote(db.Model):
    __tablename__ = 'quotes'
    
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(15), unique=True, nullable=False)  # Q51001A
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    building_id = db.Column(db.Integer, db.ForeignKey('project_buildings.id'))
    
    # Quote Details
    quote_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    option_letter = db.Column(db.String(1), default='A')  # A, B, C, D
    revision_number = db.Column(db.Integer, default=0)  # 0, 1, 2, 3
    
    # Status and Dates
    status = db.Column(db.Enum(QuoteStatus), default=QuoteStatus.DRAFT)
    quote_date = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    
    # Financial Information
    subtotal = db.Column(db.Numeric(15, 2), default=0)
    discount_amount = db.Column(db.Numeric(15, 2), default=0)
    tax_amount = db.Column(db.Numeric(15, 2), default=0)
    total_value = db.Column(db.Numeric(15, 2), default=0)
    
    # Mitek Integration
    mitek_job_number = db.Column(db.String(15))  # Links to Mitek Pamir
    variables_imported = db.Column(db.Boolean, default=False)
    
    # Audit Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    building = db.relationship('ProjectBuilding', backref='quotes')
    creator = db.relationship('User', backref='created_quotes')
    lines = db.relationship('QuoteLine', backref='quote', cascade='all, delete-orphan')
    
    def generate_quote_number(self):
        """Generate quote number in format Q51001A"""
        # Get project sequence number from project number
        project_parts = self.project.project_number.split('-')
        if len(project_parts) >= 3:
            project_seq = project_parts[2]
        else:
            project_seq = '001'
            
        # Get next quote sequence for this project
        last_quote = Quote.query.filter_by(project_id=self.project_id).order_by(Quote.quote_number.desc()).first()
        
        if last_quote and last_quote.quote_number.startswith('Q'):
            # Extract sequence from last quote
            quote_part = last_quote.quote_number[1:]  # Remove 'Q'
            if len(quote_part) >= 5:
                base_number = quote_part[:-1]  # Remove option letter
                sequence = int(base_number) + 1
            else:
                sequence = int(f'5{project_seq}1')
        else:
            sequence = int(f'5{project_seq}1')
            
        return f'Q{sequence}{self.option_letter}'

# Quote Lines
class QuoteLine(db.Model):
    __tablename__ = 'quote_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), nullable=False)
    line_number = db.Column(db.Integer, nullable=False)
    
    # Item Information
    stock_item_id = db.Column(db.Integer, db.ForeignKey('stock_items.id'))
    composite_item_id = db.Column(db.Integer, db.ForeignKey('composite_items.id'))
    description = db.Column(db.String(500), nullable=False)
    
    # Quantity and Pricing
    quantity = db.Column(db.Numeric(15, 4), nullable=False)
    unit_price = db.Column(db.Numeric(15, 4), nullable=False)
    line_total = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Formula Integration
    formula_id = db.Column(db.Integer, db.ForeignKey('formulas.id'))
    calculated_quantity = db.Column(db.Boolean, default=False)
    
    # Audit Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stock_item = db.relationship('StockItem', backref='quote_lines')
    composite_item = db.relationship('CompositeItem', backref='quote_lines')
    formula = db.relationship('Formula', backref='quote_lines')

# Tender Management
class Tender(db.Model):
    __tablename__ = 'tenders'
    
    id = db.Column(db.Integer, primary_key=True)
    tender_number = db.Column(db.String(15), unique=True, nullable=False)  # T51001A
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    
    # Tender Details
    tender_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    option_letter = db.Column(db.String(1), default='A')
    revision_number = db.Column(db.Integer, default=0)
    
    # Status and Dates
    status = db.Column(db.Enum(TenderStatus), default=TenderStatus.DRAFT)
    tender_date = db.Column(db.DateTime, default=datetime.utcnow)
    submission_date = db.Column(db.DateTime)
    closing_date = db.Column(db.DateTime)
    
    # Financial Information
    subtotal = db.Column(db.Numeric(15, 2), default=0)
    tax_amount = db.Column(db.Numeric(15, 2), default=0)
    total_value = db.Column(db.Numeric(15, 2), default=0)
    
    # Audit Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    creator = db.relationship('User', backref='created_tenders')
    assemblies = db.relationship('TenderAssembly', backref='tender', cascade='all, delete-orphan')

# Tender Assemblies (Composite rates for supply & install)
class TenderAssembly(db.Model):
    __tablename__ = 'tender_assemblies'
    
    id = db.Column(db.Integer, primary_key=True)
    tender_id = db.Column(db.Integer, db.ForeignKey('tenders.id'), nullable=False)
    assembly_number = db.Column(db.Integer, nullable=False)
    
    # Assembly Information
    composite_item_id = db.Column(db.Integer, db.ForeignKey('composite_items.id'), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    
    # Quantity and Pricing
    quantity = db.Column(db.Numeric(15, 4), nullable=False)
    unit_rate = db.Column(db.Numeric(15, 4), nullable=False)  # Supply & Install rate
    line_total = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Relationships
    composite_item = db.relationship('CompositeItem', backref='tender_assemblies')

# Order Management
class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(15), unique=True, nullable=False)  # O51001A
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'))  # Source quote
    tender_id = db.Column(db.Integer, db.ForeignKey('tenders.id'))  # Source tender
    
    # Order Details
    order_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    
    # Status and Dates
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.DRAFT)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    required_date = db.Column(db.DateTime)
    delivery_date = db.Column(db.DateTime)
    
    # Financial Information
    subtotal = db.Column(db.Numeric(15, 2), default=0)
    tax_amount = db.Column(db.Numeric(15, 2), default=0)
    total_value = db.Column(db.Numeric(15, 2), default=0)
    
    # Credit Approval
    credit_approved = db.Column(db.Boolean, default=False)
    credit_approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    credit_approved_date = db.Column(db.DateTime)
    
    # Audit Fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    source_quote = db.relationship('Quote', backref='orders')
    source_tender = db.relationship('Tender', backref='orders')
    credit_approver = db.relationship('User', foreign_keys=[credit_approved_by], backref='approved_orders')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_orders')

# Project Documents
class ProjectDocument(db.Model):
    __tablename__ = 'project_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    
    # Document Information
    document_name = db.Column(db.String(255), nullable=False)
    document_type = db.Column(db.String(50))  # Plans, Specifications, Photos, etc.
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    
    # Audit Fields
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_documents')

# Project Variables (from Mitek Pamir imports)
class ProjectVariable(db.Model):
    __tablename__ = 'project_variables'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'))
    
    # Variable Information
    variable_name = db.Column(db.String(100), nullable=False)
    variable_value = db.Column(db.String(100), nullable=False)
    variable_unit = db.Column(db.String(20))
    variable_category = db.Column(db.String(50))  # DIMENSION, AREA, COUNT, etc.
    
    # Import Information
    import_batch_id = db.Column(db.String(50))  # UUID for batch tracking
    mitek_job_number = db.Column(db.String(15))
    
    # Audit Fields
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)
    imported_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    quote = db.relationship('Quote', backref='variables')
    importer = db.relationship('User', backref='imported_variables')

