from src.models.user import db
from datetime import datetime
from decimal import Decimal
import json

class CompositeItem(db.Model):
    """
    Separate table for composite items (tender rates) with recipes
    These act like stock codes but contain multiple components
    """
    __tablename__ = 'composite_items'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    long_description = db.Column(db.Text)
    
    # Category and Type
    category = db.Column(db.String(50), nullable=False)  # ROOFING, FLASHING, STRUCTURAL, etc.
    composite_type = db.Column(db.String(50), nullable=False)  # SUPPLY_ONLY, INSTALL_ONLY, SUPPLY_INSTALL
    
    # Units and Pricing
    sales_uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'), nullable=False)
    base_selling_price = db.Column(db.Numeric(18, 4), default=0.0)  # Calculated from recipe
    markup_percentage = db.Column(db.Numeric(5, 2), default=0.0)  # Additional markup on top of recipe cost
    
    # Recipe Properties
    recipe_version = db.Column(db.Integer, default=1)
    is_recipe_locked = db.Column(db.Boolean, default=False)  # Lock recipe to prevent changes
    auto_calculate_price = db.Column(db.Boolean, default=True)  # Auto-calculate from recipe
    
    # Usage Tracking
    times_quoted = db.Column(db.Integer, default=0)
    times_ordered = db.Column(db.Integer, default=0)
    last_used_date = db.Column(db.DateTime)
    
    # Status and Audit
    is_active = db.Column(db.Boolean, default=True)
    is_standard = db.Column(db.Boolean, default=False)  # Standard composite vs custom
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))
    updated_by = db.Column(db.String(100))
    
    # Relationships
    sales_uom = db.relationship('UnitOfMeasure', backref='composite_items')
    recipe_components = db.relationship('CompositeRecipeComponent', backref='composite_item', cascade='all, delete-orphan')
    
    def calculate_recipe_cost(self):
        """Calculate total cost from recipe components"""
        total_cost = 0.0
        for component in self.recipe_components:
            if component.is_active:
                component_cost = component.calculate_component_cost()
                total_cost += component_cost
        return total_cost
    
    def calculate_selling_price(self):
        """Calculate selling price including markup"""
        recipe_cost = self.calculate_recipe_cost()
        markup_amount = recipe_cost * (float(self.markup_percentage or 0) / 100)
        return recipe_cost + markup_amount
    
    def update_usage_stats(self, usage_type='quoted'):
        """Update usage statistics"""
        if usage_type == 'quoted':
            self.times_quoted += 1
        elif usage_type == 'ordered':
            self.times_ordered += 1
        self.last_used_date = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'long_description': self.long_description,
            'category': self.category,
            'composite_type': self.composite_type,
            'sales_uom_id': self.sales_uom_id,
            'sales_uom_code': self.sales_uom.code if self.sales_uom else None,
            'base_selling_price': float(self.base_selling_price) if self.base_selling_price else 0.0,
            'markup_percentage': float(self.markup_percentage) if self.markup_percentage else 0.0,
            'recipe_version': self.recipe_version,
            'is_recipe_locked': self.is_recipe_locked,
            'auto_calculate_price': self.auto_calculate_price,
            'calculated_cost': self.calculate_recipe_cost(),
            'calculated_selling_price': self.calculate_selling_price(),
            'times_quoted': self.times_quoted,
            'times_ordered': self.times_ordered,
            'last_used_date': self.last_used_date.isoformat() if self.last_used_date else None,
            'is_active': self.is_active,
            'is_standard': self.is_standard,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'component_count': len(self.recipe_components)
        }

class CompositeRecipeComponent(db.Model):
    """
    Components that make up a composite item recipe
    """
    __tablename__ = 'composite_recipe_components'
    
    id = db.Column(db.Integer, primary_key=True)
    composite_item_id = db.Column(db.Integer, db.ForeignKey('composite_items.id'), nullable=False)
    
    # Component can be either a stock item or another composite item
    stock_item_id = db.Column(db.Integer, db.ForeignKey('advanced_stock_items.id'))
    child_composite_id = db.Column(db.Integer, db.ForeignKey('composite_items.id'))  # For nested composites
    
    # Component Details
    component_type = db.Column(db.String(20), nullable=False)  # MATERIAL, LABOUR, TRANSPORT, OVERHEAD, OTHER
    description = db.Column(db.String(200))  # Override description if needed
    
    # Quantity and UOM
    quantity_required = db.Column(db.Numeric(18, 6), nullable=False)
    uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'), nullable=False)
    
    # Costing
    unit_cost = db.Column(db.Numeric(18, 4))  # Override cost if needed
    use_current_cost = db.Column(db.Boolean, default=True)  # Use current stock cost vs fixed cost
    waste_percentage = db.Column(db.Numeric(5, 2), default=0.0)
    
    # Conditional Logic
    is_optional = db.Column(db.Boolean, default=False)
    condition_formula = db.Column(db.Text)  # Formula for when this component applies
    
    # Sequencing and Grouping
    sequence_number = db.Column(db.Integer, default=0)
    component_group = db.Column(db.String(50))  # Group related components
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stock_item = db.relationship('AdvancedStockItem', foreign_keys=[stock_item_id])
    child_composite = db.relationship('CompositeItem', foreign_keys=[child_composite_id])
    uom = db.relationship('UnitOfMeasure', backref='recipe_components')
    
    def get_effective_unit_cost(self):
        """Get the effective unit cost (current or fixed)"""
        if self.use_current_cost and self.stock_item:
            return float(self.stock_item.standard_cost or 0.0)
        elif self.use_current_cost and self.child_composite:
            return self.child_composite.calculate_selling_price()
        else:
            return float(self.unit_cost or 0.0)
    
    def calculate_component_cost(self):
        """Calculate total cost for this component including waste"""
        unit_cost = self.get_effective_unit_cost()
        base_cost = unit_cost * float(self.quantity_required)
        waste_amount = base_cost * (float(self.waste_percentage or 0) / 100)
        return base_cost + waste_amount
    
    def to_dict(self):
        return {
            'id': self.id,
            'composite_item_id': self.composite_item_id,
            'stock_item_id': self.stock_item_id,
            'stock_item_code': self.stock_item.full_code if self.stock_item else None,
            'stock_item_description': self.stock_item.description if self.stock_item else None,
            'child_composite_id': self.child_composite_id,
            'child_composite_code': self.child_composite.code if self.child_composite else None,
            'component_type': self.component_type,
            'description': self.description,
            'quantity_required': float(self.quantity_required),
            'uom_id': self.uom_id,
            'uom_code': self.uom.code if self.uom else None,
            'unit_cost': float(self.unit_cost) if self.unit_cost else None,
            'effective_unit_cost': self.get_effective_unit_cost(),
            'use_current_cost': self.use_current_cost,
            'waste_percentage': float(self.waste_percentage) if self.waste_percentage else 0.0,
            'calculated_cost': self.calculate_component_cost(),
            'is_optional': self.is_optional,
            'condition_formula': self.condition_formula,
            'sequence_number': self.sequence_number,
            'component_group': self.component_group,
            'is_active': self.is_active,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

class DynamicBOM(db.Model):
    """
    Dynamic BOMs for manufactured items like timber trusses
    These are created per quote/order and are unique
    """
    __tablename__ = 'dynamic_boms'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Reference Information
    reference_type = db.Column(db.String(20), nullable=False)  # QUOTE, ORDER, PROJECT
    reference_id = db.Column(db.Integer, nullable=False)  # ID of the quote/order/project
    reference_number = db.Column(db.String(50))  # Quote/Order number for easy reference
    
    # Product Information
    product_code = db.Column(db.String(100), nullable=False)  # Generated product code
    product_description = db.Column(db.String(500), nullable=False)
    product_category = db.Column(db.String(50), default='MANUFACTURED')
    
    # Manufacturing Details
    manufacturing_method = db.Column(db.String(50))  # CUT_TO_SIZE, FABRICATED, ASSEMBLED
    estimated_manufacturing_time = db.Column(db.Numeric(8, 2))  # Hours
    complexity_rating = db.Column(db.String(20))  # SIMPLE, MEDIUM, COMPLEX, CUSTOM
    
    # Quantities and UOM
    quantity_required = db.Column(db.Numeric(18, 4), nullable=False)
    base_uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'), nullable=False)
    
    # Costing
    material_cost = db.Column(db.Numeric(18, 4), default=0.0)
    labour_cost = db.Column(db.Numeric(18, 4), default=0.0)
    overhead_cost = db.Column(db.Numeric(18, 4), default=0.0)
    total_cost = db.Column(db.Numeric(18, 4), default=0.0)
    
    # Design/Engineering Data (from Mitek Pamir)
    design_data = db.Column(db.JSON)  # Store Pamir export data
    engineering_notes = db.Column(db.Text)
    
    # Status and Workflow
    bom_status = db.Column(db.String(20), default='DRAFT')  # DRAFT, APPROVED, LOCKED, OBSOLETE
    approval_required = db.Column(db.Boolean, default=True)
    approved_by = db.Column(db.String(100))
    approved_date = db.Column(db.DateTime)
    
    # Version Control
    version_number = db.Column(db.Integer, default=1)
    parent_bom_id = db.Column(db.Integer, db.ForeignKey('dynamic_boms.id'))  # For revisions
    is_current_version = db.Column(db.Boolean, default=True)
    
    # Audit
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))
    updated_by = db.Column(db.String(100))
    
    # Relationships
    base_uom = db.relationship('UnitOfMeasure', backref='dynamic_boms')
    parent_bom = db.relationship('DynamicBOM', remote_side=[id], backref='revisions')
    components = db.relationship('DynamicBOMComponent', backref='dynamic_bom', cascade='all, delete-orphan')
    
    def calculate_costs(self):
        """Calculate all costs from components"""
        material_cost = 0.0
        labour_cost = 0.0
        overhead_cost = 0.0
        
        for component in self.components:
            if component.is_active:
                component_cost = component.calculate_total_cost()
                
                if component.component_type == 'MATERIAL':
                    material_cost += component_cost
                elif component.component_type == 'LABOUR':
                    labour_cost += component_cost
                elif component.component_type in ['OVERHEAD', 'TRANSPORT', 'OTHER']:
                    overhead_cost += component_cost
        
        self.material_cost = material_cost
        self.labour_cost = labour_cost
        self.overhead_cost = overhead_cost
        self.total_cost = material_cost + labour_cost + overhead_cost
        
        return {
            'material_cost': material_cost,
            'labour_cost': labour_cost,
            'overhead_cost': overhead_cost,
            'total_cost': self.total_cost
        }
    
    def create_revision(self, updated_by):
        """Create a new revision of this BOM"""
        # Mark current version as not current
        self.is_current_version = False
        
        # Create new revision
        new_bom = DynamicBOM(
            reference_type=self.reference_type,
            reference_id=self.reference_id,
            reference_number=self.reference_number,
            product_code=self.product_code,
            product_description=self.product_description,
            product_category=self.product_category,
            manufacturing_method=self.manufacturing_method,
            estimated_manufacturing_time=self.estimated_manufacturing_time,
            complexity_rating=self.complexity_rating,
            quantity_required=self.quantity_required,
            base_uom_id=self.base_uom_id,
            design_data=self.design_data,
            engineering_notes=self.engineering_notes,
            version_number=self.version_number + 1,
            parent_bom_id=self.id,
            is_current_version=True,
            created_by=updated_by,
            updated_by=updated_by
        )
        
        db.session.add(new_bom)
        db.session.flush()  # Get the new ID
        
        # Copy components
        for component in self.components:
            new_component = DynamicBOMComponent(
                dynamic_bom_id=new_bom.id,
                stock_item_id=component.stock_item_id,
                component_type=component.component_type,
                description=component.description,
                quantity_required=component.quantity_required,
                uom_id=component.uom_id,
                unit_cost=component.unit_cost,
                waste_percentage=component.waste_percentage,
                sequence_number=component.sequence_number,
                notes=component.notes,
                is_active=component.is_active
            )
            db.session.add(new_component)
        
        return new_bom
    
    def to_dict(self):
        return {
            'id': self.id,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'reference_number': self.reference_number,
            'product_code': self.product_code,
            'product_description': self.product_description,
            'product_category': self.product_category,
            'manufacturing_method': self.manufacturing_method,
            'estimated_manufacturing_time': float(self.estimated_manufacturing_time) if self.estimated_manufacturing_time else None,
            'complexity_rating': self.complexity_rating,
            'quantity_required': float(self.quantity_required),
            'base_uom_id': self.base_uom_id,
            'base_uom_code': self.base_uom.code if self.base_uom else None,
            'material_cost': float(self.material_cost) if self.material_cost else 0.0,
            'labour_cost': float(self.labour_cost) if self.labour_cost else 0.0,
            'overhead_cost': float(self.overhead_cost) if self.overhead_cost else 0.0,
            'total_cost': float(self.total_cost) if self.total_cost else 0.0,
            'design_data': self.design_data,
            'engineering_notes': self.engineering_notes,
            'bom_status': self.bom_status,
            'approval_required': self.approval_required,
            'approved_by': self.approved_by,
            'approved_date': self.approved_date.isoformat() if self.approved_date else None,
            'version_number': self.version_number,
            'parent_bom_id': self.parent_bom_id,
            'is_current_version': self.is_current_version,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'component_count': len(self.components)
        }

class DynamicBOMComponent(db.Model):
    """
    Components for dynamic BOMs
    """
    __tablename__ = 'dynamic_bom_components'
    
    id = db.Column(db.Integer, primary_key=True)
    dynamic_bom_id = db.Column(db.Integer, db.ForeignKey('dynamic_boms.id'), nullable=False)
    stock_item_id = db.Column(db.Integer, db.ForeignKey('advanced_stock_items.id'), nullable=False)
    
    # Component Details
    component_type = db.Column(db.String(20), nullable=False)  # MATERIAL, LABOUR, TRANSPORT, OVERHEAD, OTHER
    description = db.Column(db.String(200))  # Override description if needed
    
    # Quantity and UOM
    quantity_required = db.Column(db.Numeric(18, 6), nullable=False)
    uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'), nullable=False)
    
    # Costing (captured at time of BOM creation)
    unit_cost = db.Column(db.Numeric(18, 4), nullable=False)
    waste_percentage = db.Column(db.Numeric(5, 2), default=0.0)
    
    # Cutting/Processing Details (for timber)
    cut_length = db.Column(db.Numeric(10, 3))  # For cut-to-length items
    cut_angle = db.Column(db.Numeric(5, 2))  # Cutting angle if applicable
    processing_notes = db.Column(db.Text)
    
    # Sequencing
    sequence_number = db.Column(db.Integer, default=0)
    assembly_stage = db.Column(db.String(50))  # PREPARATION, ASSEMBLY, FINISHING
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stock_item = db.relationship('AdvancedStockItem', backref='dynamic_bom_usages')
    uom = db.relationship('UnitOfMeasure', backref='dynamic_bom_components')
    
    def calculate_total_cost(self):
        """Calculate total cost including waste"""
        base_cost = float(self.unit_cost) * float(self.quantity_required)
        waste_amount = base_cost * (float(self.waste_percentage or 0) / 100)
        return base_cost + waste_amount
    
    def to_dict(self):
        return {
            'id': self.id,
            'dynamic_bom_id': self.dynamic_bom_id,
            'stock_item_id': self.stock_item_id,
            'stock_item_code': self.stock_item.full_code if self.stock_item else None,
            'stock_item_description': self.stock_item.description if self.stock_item else None,
            'component_type': self.component_type,
            'description': self.description,
            'quantity_required': float(self.quantity_required),
            'uom_id': self.uom_id,
            'uom_code': self.uom.code if self.uom else None,
            'unit_cost': float(self.unit_cost),
            'waste_percentage': float(self.waste_percentage) if self.waste_percentage else 0.0,
            'total_cost': self.calculate_total_cost(),
            'cut_length': float(self.cut_length) if self.cut_length else None,
            'cut_angle': float(self.cut_angle) if self.cut_angle else None,
            'processing_notes': self.processing_notes,
            'sequence_number': self.sequence_number,
            'assembly_stage': self.assembly_stage,
            'is_active': self.is_active,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

