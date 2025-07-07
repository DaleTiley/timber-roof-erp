from src.models.user import db
from datetime import datetime
from decimal import Decimal
import json
import re
import math

class Formula(db.Model):
    """
    Formula definitions that can be assigned to stock items
    """
    __tablename__ = 'formulas'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Information
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # TIMBER, SHEETING, FLASHING, GENERAL, etc.
    
    # Formula Definition
    formula_expression = db.Column(db.Text, nullable=False)  # The actual formula
    result_uom_id = db.Column(db.Integer, db.ForeignKey('units_of_measure.id'))  # UOM of the result
    
    # Formula Properties
    formula_type = db.Column(db.String(20), default='QUANTITY')  # QUANTITY, LENGTH, AREA, VOLUME, COUNT
    precision_digits = db.Column(db.Integer, default=2)  # Decimal places for result
    always_round_up = db.Column(db.Boolean, default=False)  # Always round up (like ROUNDUP function)
    minimum_value = db.Column(db.Numeric(18, 6))  # Minimum result value
    maximum_value = db.Column(db.Numeric(18, 6))  # Maximum result value
    
    # Variables Used
    required_variables = db.Column(db.JSON)  # List of variable names required by this formula
    optional_variables = db.Column(db.JSON)  # List of optional variable names
    
    # Testing and Validation
    test_scenarios = db.Column(db.JSON)  # Test cases with input/expected output
    last_test_date = db.Column(db.DateTime)
    last_test_result = db.Column(db.String(20))  # PASSED, FAILED, NOT_TESTED
    test_notes = db.Column(db.Text)
    
    # Usage and Performance
    times_used = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Numeric(5, 2), default=100.0)  # Percentage of successful calculations
    average_execution_time = db.Column(db.Numeric(8, 4))  # Milliseconds
    
    # Status and Lifecycle
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)
    approval_required = db.Column(db.Boolean, default=True)
    approved_by = db.Column(db.String(100))
    approved_date = db.Column(db.DateTime)
    
    # Version Control
    version_number = db.Column(db.Integer, default=1)
    parent_formula_id = db.Column(db.Integer, db.ForeignKey('formulas.id'))
    is_current_version = db.Column(db.Boolean, default=True)
    
    # Audit
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))
    updated_by = db.Column(db.String(100))
    
    # Relationships
    result_uom = db.relationship('UnitOfMeasure', backref='formulas')
    parent_formula = db.relationship('Formula', remote_side=[id], backref='versions')
    stock_assignments = db.relationship('StockFormulaAssignment', backref='formula', cascade='all, delete-orphan')
    calculation_logs = db.relationship('FormulaCalculationLog', backref='formula', cascade='all, delete-orphan')
    
    def validate_formula_syntax(self):
        """Validate the formula syntax and return any errors"""
        try:
            # Basic syntax validation
            if not self.formula_expression:
                return False, "Formula expression is empty"
            
            # Check for balanced parentheses
            if self.formula_expression.count('(') != self.formula_expression.count(')'):
                return False, "Unbalanced parentheses in formula"
            
            # Check for valid function names
            valid_functions = ['ROUNDUP', 'ROUNDDOWN', 'ROUND', 'CEILING', 'FLOOR', 'ABS', 'MAX', 'MIN', 'IF', 'SUM', 'AVERAGE']
            
            # Extract function calls
            function_pattern = r'([A-Z_]+)\s*\('
            functions_used = re.findall(function_pattern, self.formula_expression)
            
            for func in functions_used:
                if func not in valid_functions:
                    return False, f"Unknown function: {func}"
            
            # Check for valid variable syntax
            variable_pattern = r'\{([^}]+)\}'
            variables_used = re.findall(variable_pattern, self.formula_expression)
            
            # Update required variables if not set
            if not self.required_variables:
                self.required_variables = variables_used
            
            return True, "Formula syntax is valid"
            
        except Exception as e:
            return False, f"Syntax validation error: {str(e)}"
    
    def test_formula(self, test_variables):
        """Test the formula with provided variables"""
        try:
            result = self.calculate(test_variables)
            return True, result, None
        except Exception as e:
            return False, None, str(e)
    
    def calculate(self, variables):
        """Calculate the formula result using provided variables"""
        try:
            # Start timing
            start_time = datetime.utcnow()
            
            # Prepare the formula expression
            expression = self.formula_expression
            
            # Replace variables with values
            for var_name, var_value in variables.items():
                # Replace {Variable Name} with actual value
                pattern = r'\{' + re.escape(var_name) + r'\}'
                expression = re.sub(pattern, str(var_value), expression)
            
            # Check if all required variables are provided
            remaining_vars = re.findall(r'\{([^}]+)\}', expression)
            if remaining_vars:
                missing_vars = [var for var in remaining_vars if var in (self.required_variables or [])]
                if missing_vars:
                    raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
            
            # Replace function calls with Python equivalents
            expression = self._replace_formula_functions(expression)
            
            # Evaluate the expression safely
            result = self._safe_eval(expression)
            
            # Apply rounding and constraints
            result = self._apply_result_constraints(result)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000
            
            # Update usage statistics
            self.times_used += 1
            if self.average_execution_time:
                self.average_execution_time = (self.average_execution_time + execution_time) / 2
            else:
                self.average_execution_time = execution_time
            
            # Log the calculation
            log_entry = FormulaCalculationLog(
                formula_id=self.id,
                input_variables=variables,
                calculated_result=float(result),
                execution_time_ms=execution_time,
                was_successful=True,
                calculation_date=datetime.utcnow()
            )
            db.session.add(log_entry)
            
            return float(result)
            
        except Exception as e:
            # Log the failed calculation
            log_entry = FormulaCalculationLog(
                formula_id=self.id,
                input_variables=variables,
                error_message=str(e),
                was_successful=False,
                calculation_date=datetime.utcnow()
            )
            db.session.add(log_entry)
            
            # Update success rate
            total_calculations = self.times_used + 1
            successful_calculations = total_calculations - len([log for log in self.calculation_logs if not log.was_successful])
            self.success_rate = (successful_calculations / total_calculations) * 100
            
            raise e
    
    def _replace_formula_functions(self, expression):
        """Replace formula functions with Python equivalents"""
        # ROUNDUP function
        expression = re.sub(r'ROUNDUP\s*\(\s*([^,]+)\s*,\s*(\d+)\s*\)', r'math.ceil(\1 * 10**\2) / 10**\2', expression)
        
        # ROUNDDOWN function  
        expression = re.sub(r'ROUNDDOWN\s*\(\s*([^,]+)\s*,\s*(\d+)\s*\)', r'math.floor(\1 * 10**\2) / 10**\2', expression)
        
        # ROUND function
        expression = re.sub(r'ROUND\s*\(\s*([^,]+)\s*,\s*(\d+)\s*\)', r'round(\1, \2)', expression)
        
        # CEILING function
        expression = re.sub(r'CEILING\s*\(\s*([^,]+)\s*\)', r'math.ceil(\1)', expression)
        
        # FLOOR function
        expression = re.sub(r'FLOOR\s*\(\s*([^,]+)\s*\)', r'math.floor(\1)', expression)
        
        # ABS function
        expression = re.sub(r'ABS\s*\(\s*([^,]+)\s*\)', r'abs(\1)', expression)
        
        # MAX function
        expression = re.sub(r'MAX\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*\)', r'max(\1, \2)', expression)
        
        # MIN function
        expression = re.sub(r'MIN\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*\)', r'min(\1, \2)', expression)
        
        return expression
    
    def _safe_eval(self, expression):
        """Safely evaluate a mathematical expression"""
        # Only allow safe operations and functions
        allowed_names = {
            "__builtins__": {},
            "math": math,
            "abs": abs,
            "max": max,
            "min": min,
            "round": round,
            "sum": sum,
            "len": len
        }
        
        # Remove any potentially dangerous operations
        dangerous_patterns = [
            r'__\w+__',  # Dunder methods
            r'import\s+',  # Import statements
            r'exec\s*\(',  # Exec function
            r'eval\s*\(',  # Eval function
            r'open\s*\(',  # File operations
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, expression):
                raise ValueError(f"Dangerous operation detected in formula: {pattern}")
        
        return eval(expression, allowed_names)
    
    def _apply_result_constraints(self, result):
        """Apply rounding and value constraints to the result"""
        # Apply rounding
        if self.always_round_up:
            result = math.ceil(result)
        else:
            result = round(result, self.precision_digits or 2)
        
        # Apply minimum value constraint
        if self.minimum_value and result < float(self.minimum_value):
            result = float(self.minimum_value)
        
        # Apply maximum value constraint
        if self.maximum_value and result > float(self.maximum_value):
            result = float(self.maximum_value)
        
        return result
    
    def create_version(self, updated_by):
        """Create a new version of this formula"""
        # Mark current version as not current
        self.is_current_version = False
        
        # Create new version
        new_formula = Formula(
            name=self.name,
            code=self.code,
            description=self.description,
            category=self.category,
            formula_expression=self.formula_expression,
            result_uom_id=self.result_uom_id,
            formula_type=self.formula_type,
            precision_digits=self.precision_digits,
            always_round_up=self.always_round_up,
            minimum_value=self.minimum_value,
            maximum_value=self.maximum_value,
            required_variables=self.required_variables,
            optional_variables=self.optional_variables,
            test_scenarios=self.test_scenarios,
            version_number=self.version_number + 1,
            parent_formula_id=self.id,
            is_current_version=True,
            created_by=updated_by,
            updated_by=updated_by
        )
        
        db.session.add(new_formula)
        return new_formula
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'category': self.category,
            'formula_expression': self.formula_expression,
            'result_uom_id': self.result_uom_id,
            'result_uom_code': self.result_uom.code if self.result_uom else None,
            'formula_type': self.formula_type,
            'precision_digits': self.precision_digits,
            'always_round_up': self.always_round_up,
            'minimum_value': float(self.minimum_value) if self.minimum_value else None,
            'maximum_value': float(self.maximum_value) if self.maximum_value else None,
            'required_variables': self.required_variables,
            'optional_variables': self.optional_variables,
            'test_scenarios': self.test_scenarios,
            'last_test_date': self.last_test_date.isoformat() if self.last_test_date else None,
            'last_test_result': self.last_test_result,
            'test_notes': self.test_notes,
            'times_used': self.times_used,
            'success_rate': float(self.success_rate) if self.success_rate else 100.0,
            'average_execution_time': float(self.average_execution_time) if self.average_execution_time else None,
            'is_active': self.is_active,
            'is_approved': self.is_approved,
            'approval_required': self.approval_required,
            'approved_by': self.approved_by,
            'approved_date': self.approved_date.isoformat() if self.approved_date else None,
            'version_number': self.version_number,
            'parent_formula_id': self.parent_formula_id,
            'is_current_version': self.is_current_version,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'stock_assignments_count': len(self.stock_assignments)
        }

class StockFormulaAssignment(db.Model):
    """
    Assignment of formulas to stock items
    """
    __tablename__ = 'stock_formula_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_item_id = db.Column(db.Integer, db.ForeignKey('advanced_stock_items.id'), nullable=False)
    formula_id = db.Column(db.Integer, db.ForeignKey('formulas.id'), nullable=False)
    
    # Assignment Properties
    is_primary = db.Column(db.Boolean, default=True)  # Primary formula for this stock item
    priority = db.Column(db.Integer, default=1)  # Priority if multiple formulas
    
    # Conditions for when this formula applies
    condition_expression = db.Column(db.Text)  # Optional condition for when to use this formula
    applies_to_quotes = db.Column(db.Boolean, default=True)
    applies_to_tenders = db.Column(db.Boolean, default=True)
    applies_to_orders = db.Column(db.Boolean, default=True)
    
    # Override Settings
    override_minimum_qty = db.Column(db.Numeric(18, 6))  # Override minimum quantity
    override_maximum_qty = db.Column(db.Numeric(18, 6))  # Override maximum quantity
    waste_factor = db.Column(db.Numeric(5, 2), default=0.0)  # Additional waste percentage
    
    # Status and Audit
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))
    updated_by = db.Column(db.String(100))
    
    # Relationships
    stock_item = db.relationship('AdvancedStockItem', backref='formula_assignments')
    
    def calculate_quantity(self, variables):
        """Calculate quantity using the assigned formula"""
        try:
            # Calculate base quantity using formula
            base_qty = self.formula.calculate(variables)
            
            # Apply waste factor
            if self.waste_factor:
                waste_amount = base_qty * (float(self.waste_factor) / 100)
                base_qty += waste_amount
            
            # Apply minimum/maximum overrides
            if self.override_minimum_qty and base_qty < float(self.override_minimum_qty):
                base_qty = float(self.override_minimum_qty)
            
            if self.override_maximum_qty and base_qty > float(self.override_maximum_qty):
                base_qty = float(self.override_maximum_qty)
            
            return base_qty
            
        except Exception as e:
            raise Exception(f"Error calculating quantity for {self.stock_item.full_code}: {str(e)}")
    
    def to_dict(self):
        return {
            'id': self.id,
            'stock_item_id': self.stock_item_id,
            'stock_item_code': self.stock_item.full_code if self.stock_item else None,
            'formula_id': self.formula_id,
            'formula_name': self.formula.name if self.formula else None,
            'formula_code': self.formula.code if self.formula else None,
            'is_primary': self.is_primary,
            'priority': self.priority,
            'condition_expression': self.condition_expression,
            'applies_to_quotes': self.applies_to_quotes,
            'applies_to_tenders': self.applies_to_tenders,
            'applies_to_orders': self.applies_to_orders,
            'override_minimum_qty': float(self.override_minimum_qty) if self.override_minimum_qty else None,
            'override_maximum_qty': float(self.override_maximum_qty) if self.override_maximum_qty else None,
            'waste_factor': float(self.waste_factor) if self.waste_factor else 0.0,
            'is_active': self.is_active,
            'notes': self.notes,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by
        }

class ProjectVariable(db.Model):
    """
    Variables imported from Mitek Pamir for specific projects/quotes/orders
    """
    __tablename__ = 'project_variables'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Reference Information
    reference_type = db.Column(db.String(20), nullable=False)  # QUOTE, TENDER, ORDER, PROJECT
    reference_id = db.Column(db.Integer, nullable=False)
    reference_number = db.Column(db.String(50))
    
    # Variable Definition
    variable_name = db.Column(db.String(100), nullable=False)
    variable_value = db.Column(db.Numeric(18, 6), nullable=False)
    variable_unit = db.Column(db.String(20))  # Unit of measurement
    variable_type = db.Column(db.String(20), default='NUMERIC')  # NUMERIC, TEXT, BOOLEAN
    
    # Source Information
    source_system = db.Column(db.String(50), default='MITEK_PAMIR')
    source_file = db.Column(db.String(200))  # Original file name
    import_batch_id = db.Column(db.String(50))  # Batch identifier for grouped imports
    
    # Variable Properties
    category = db.Column(db.String(50))  # DIMENSION, AREA, LENGTH, COUNT, etc.
    description = db.Column(db.String(200))
    is_calculated = db.Column(db.Boolean, default=False)  # Was this calculated from other variables
    calculation_formula = db.Column(db.Text)  # Formula used if calculated
    
    # Usage Tracking
    times_used_in_formulas = db.Column(db.Integer, default=0)
    last_used_date = db.Column(db.DateTime)
    
    # Status and Audit
    is_active = db.Column(db.Boolean, default=True)
    import_date = db.Column(db.DateTime, default=datetime.utcnow)
    imported_by = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'reference_number': self.reference_number,
            'variable_name': self.variable_name,
            'variable_value': float(self.variable_value),
            'variable_unit': self.variable_unit,
            'variable_type': self.variable_type,
            'source_system': self.source_system,
            'source_file': self.source_file,
            'import_batch_id': self.import_batch_id,
            'category': self.category,
            'description': self.description,
            'is_calculated': self.is_calculated,
            'calculation_formula': self.calculation_formula,
            'times_used_in_formulas': self.times_used_in_formulas,
            'last_used_date': self.last_used_date.isoformat() if self.last_used_date else None,
            'is_active': self.is_active,
            'import_date': self.import_date.isoformat() if self.import_date else None,
            'imported_by': self.imported_by,
            'notes': self.notes
        }

class FormulaCalculationLog(db.Model):
    """
    Log of formula calculations for debugging and performance monitoring
    """
    __tablename__ = 'formula_calculation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    formula_id = db.Column(db.Integer, db.ForeignKey('formulas.id'), nullable=False)
    
    # Calculation Details
    input_variables = db.Column(db.JSON)  # Variables used in calculation
    calculated_result = db.Column(db.Numeric(18, 6))
    execution_time_ms = db.Column(db.Numeric(8, 4))
    
    # Context Information
    reference_type = db.Column(db.String(20))  # QUOTE, TENDER, ORDER
    reference_id = db.Column(db.Integer)
    stock_item_id = db.Column(db.Integer, db.ForeignKey('advanced_stock_items.id'))
    
    # Result Status
    was_successful = db.Column(db.Boolean, nullable=False)
    error_message = db.Column(db.Text)
    warning_messages = db.Column(db.JSON)  # Array of warning messages
    
    # Audit
    calculation_date = db.Column(db.DateTime, default=datetime.utcnow)
    calculated_by = db.Column(db.String(100))
    
    # Relationships
    stock_item = db.relationship('AdvancedStockItem', backref='formula_calculation_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'formula_id': self.formula_id,
            'formula_name': self.formula.name if self.formula else None,
            'input_variables': self.input_variables,
            'calculated_result': float(self.calculated_result) if self.calculated_result else None,
            'execution_time_ms': float(self.execution_time_ms) if self.execution_time_ms else None,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'stock_item_id': self.stock_item_id,
            'stock_item_code': self.stock_item.full_code if self.stock_item else None,
            'was_successful': self.was_successful,
            'error_message': self.error_message,
            'warning_messages': self.warning_messages,
            'calculation_date': self.calculation_date.isoformat() if self.calculation_date else None,
            'calculated_by': self.calculated_by
        }

