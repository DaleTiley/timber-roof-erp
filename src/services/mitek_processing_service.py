import json
from decimal import Decimal
from src.models.user import db
from src.models.mitek_structure import (
    MitekJobStructure, MitekTruss, MitekTrussMember, MitekTrussPlate,
    MitekInfill, MitekHanger, MitekSundryContainer, MitekSundryItem,
    NailAggregation, QuoteLineItem
)
from src.models.formula_system import Formula
from src.models.project_hierarchy import ProjectVariable

class MitekProcessingService:
    """Service for processing Mitek job structures and creating quote line items"""
    
    @staticmethod
    def process_mitek_job(job_structure_id, quote_id, user_id):
        """Process a Mitek job structure and create quote line items"""
        try:
            job_structure = MitekJobStructure.query.get(job_structure_id)
            if not job_structure:
                return {'success': False, 'error': 'Job structure not found'}
            
            # Clear existing quote line items for this quote
            QuoteLineItem.query.filter_by(quote_id=quote_id).delete()
            
            line_number = 1
            created_items = []
            
            # Process Trusses
            if job_structure.has_trusses:
                for truss in job_structure.trusses:
                    line_item = MitekProcessingService._create_truss_line_item(
                        quote_id, truss, line_number
                    )
                    if line_item:
                        db.session.add(line_item)
                        created_items.append(line_item)
                        line_number += 1
            
            # Process Infill
            if job_structure.has_infill:
                for infill in job_structure.infill_items:
                    line_item = MitekProcessingService._create_infill_line_item(
                        quote_id, infill, line_number
                    )
                    if line_item:
                        db.session.add(line_item)
                        created_items.append(line_item)
                        line_number += 1
            
            # Process Hangers
            if job_structure.has_hangers:
                for hanger in job_structure.hangers:
                    line_item = MitekProcessingService._create_hanger_line_item(
                        quote_id, hanger, line_number
                    )
                    if line_item:
                        db.session.add(line_item)
                        created_items.append(line_item)
                        line_number += 1
            
            # Process Sundry Containers
            for container in job_structure.sundry_containers:
                container_items = MitekProcessingService._process_sundry_container(
                    quote_id, container, line_number, job_structure.project_id
                )
                for item in container_items:
                    db.session.add(item)
                    created_items.append(item)
                    line_number += 1
            
            # Aggregate and process nails
            nail_items = MitekProcessingService._aggregate_nails(
                job_structure_id, quote_id, line_number
            )
            for item in nail_items:
                db.session.add(item)
                created_items.append(item)
                line_number += 1
            
            # Update job structure status
            job_structure.status = 'processed'
            
            db.session.commit()
            
            return {
                'success': True,
                'created_items': len(created_items),
                'message': f'Successfully processed {len(created_items)} line items'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to process Mitek job: {str(e)}'
            }
    
    @staticmethod
    def _create_truss_line_item(quote_id, truss, line_number):
        """Create a quote line item for a truss"""
        description = f"Truss {truss.truss_mark} - {truss.truss_type}"
        if truss.span:
            description += f" (Span: {truss.span}m)"
        
        return QuoteLineItem(
            quote_id=quote_id,
            line_number=line_number,
            item_type='mitek_truss',
            mitek_truss_id=truss.id,
            description=description,
            quantity=truss.quantity,
            unit='ea',
            unit_price=0,  # To be calculated based on stock items and formulas
            line_total=0
        )
    
    @staticmethod
    def _create_infill_line_item(quote_id, infill, line_number):
        """Create a quote line item for infill timber"""
        description = f"Infill {infill.infill_mark} - {infill.timber_size} x {infill.length}m"
        
        return QuoteLineItem(
            quote_id=quote_id,
            line_number=line_number,
            item_type='mitek_infill',
            mitek_infill_id=infill.id,
            description=description,
            quantity=infill.quantity,
            unit='ea',
            unit_price=0,
            line_total=0
        )
    
    @staticmethod
    def _create_hanger_line_item(quote_id, hanger, line_number):
        """Create a quote line item for hangers"""
        description = f"Hanger {hanger.hanger_type}"
        if hanger.description:
            description += f" - {hanger.description}"
        
        return QuoteLineItem(
            quote_id=quote_id,
            line_number=line_number,
            item_type='mitek_hanger',
            mitek_hanger_id=hanger.id,
            description=description,
            quantity=hanger.quantity,
            unit='ea',
            unit_price=0,
            line_total=0
        )
    
    @staticmethod
    def _process_sundry_container(quote_id, container, start_line_number, project_id):
        """Process a sundry container and create line items for items with quantities > 0"""
        line_items = []
        line_number = start_line_number
        
        for sundry_item in container.items:
            # Calculate quantity using formula if available
            calculated_qty = MitekProcessingService._calculate_sundry_quantity(
                sundry_item, project_id
            )
            
            # Update the calculated quantity
            sundry_item.calculated_quantity = calculated_qty
            
            # Only create line item if quantity > 0
            if calculated_qty > 0:
                line_item = QuoteLineItem(
                    quote_id=quote_id,
                    line_number=line_number,
                    item_type='mitek_sundry',
                    mitek_sundry_item_id=sundry_item.id,
                    description=f"{container.container_name} - {sundry_item.item_description}",
                    quantity=calculated_qty,
                    unit=sundry_item.calculated_unit,
                    unit_price=0,
                    line_total=0
                )
                line_items.append(line_item)
                line_number += 1
        
        return line_items
    
    @staticmethod
    def _calculate_sundry_quantity(sundry_item, project_id):
        """Calculate quantity for a sundry item using its assigned formula"""
        if not sundry_item.formula_id:
            return Decimal('0')
        
        try:
            formula = Formula.query.get(sundry_item.formula_id)
            if not formula or formula.status != 'approved':
                return Decimal('0')
            
            # Get project variables
            variables = ProjectVariable.query.filter_by(project_id=project_id).all()
            variable_dict = {var.variable_name: float(var.variable_value) for var in variables}
            
            # Execute formula (simplified - would need proper formula engine)
            result = MitekProcessingService._execute_formula(formula.formula_expression, variable_dict)
            
            # Store calculation details
            calculation_details = {
                'formula_expression': formula.formula_expression,
                'variables_used': variable_dict,
                'result': result,
                'calculated_at': datetime.utcnow().isoformat()
            }
            sundry_item.formula_result = json.dumps(calculation_details)
            
            return Decimal(str(result)) if result > 0 else Decimal('0')
            
        except Exception as e:
            # Log error and return 0
            print(f"Error calculating quantity for sundry item {sundry_item.id}: {str(e)}")
            return Decimal('0')
    
    @staticmethod
    def _execute_formula(formula_expression, variables):
        """Execute a formula with given variables (simplified implementation)"""
        # This is a simplified implementation
        # In production, you'd use a proper formula engine with security measures
        try:
            # Replace variable placeholders with actual values
            expression = formula_expression
            for var_name, var_value in variables.items():
                expression = expression.replace(f"{{{var_name}}}", str(var_value))
            
            # Basic math functions
            import math
            safe_dict = {
                "__builtins__": {},
                "ROUNDUP": lambda x, decimals: math.ceil(x * (10 ** decimals)) / (10 ** decimals),
                "ROUNDDOWN": lambda x, decimals: math.floor(x * (10 ** decimals)) / (10 ** decimals),
                "ROUND": round,
                "CEILING": math.ceil,
                "FLOOR": math.floor,
                "ABS": abs,
                "MAX": max,
                "MIN": min,
                "math": math
            }
            
            result = eval(expression, safe_dict)
            return float(result) if result is not None else 0
            
        except Exception as e:
            print(f"Formula execution error: {str(e)}")
            return 0
    
    @staticmethod
    def _aggregate_nails(job_structure_id, quote_id, start_line_number):
        """Aggregate all nail quantities and create consolidated line items"""
        # Clear existing nail aggregations for this job
        NailAggregation.query.filter_by(job_structure_id=job_structure_id).delete()
        
        nail_totals = {}
        line_items = []
        
        # Get all sundry items that are nails
        job_structure = MitekJobStructure.query.get(job_structure_id)
        
        for container in job_structure.sundry_containers:
            for item in container.items:
                if item.item_category == 'nails' and item.calculated_quantity > 0:
                    nail_key = f"{item.item_code}_{item.item_description}"
                    
                    if nail_key not in nail_totals:
                        nail_totals[nail_key] = {
                            'nail_type': item.item_description,
                            'nail_size': item.item_code,
                            'total_ea': 0,
                            'sources': []
                        }
                    
                    nail_totals[nail_key]['total_ea'] += int(item.calculated_quantity)
                    nail_totals[nail_key]['sources'].append({
                        'container': container.container_name,
                        'item': item.item_description,
                        'quantity': int(item.calculated_quantity)
                    })
        
        # Create nail aggregation records and line items
        line_number = start_line_number
        for nail_key, nail_data in nail_totals.items():
            # Convert pieces to kg (example conversion - would be configurable)
            pieces_per_kg = MitekProcessingService._get_pieces_per_kg(nail_data['nail_size'])
            total_kg = nail_data['total_ea'] / pieces_per_kg
            
            # Create aggregation record
            aggregation = NailAggregation(
                job_structure_id=job_structure_id,
                nail_type=nail_data['nail_type'],
                nail_size=nail_data['nail_size'],
                total_quantity_ea=nail_data['total_ea'],
                total_quantity_kg=Decimal(str(total_kg)),
                pieces_per_kg=pieces_per_kg,
                source_components=json.dumps(nail_data['sources'])
            )
            db.session.add(aggregation)
            db.session.flush()  # Get the ID
            
            # Create quote line item
            line_item = QuoteLineItem(
                quote_id=quote_id,
                line_number=line_number,
                item_type='nail_aggregation',
                nail_aggregation_id=aggregation.id,
                description=f"Nails - {nail_data['nail_type']} ({nail_data['total_ea']} pcs)",
                quantity=Decimal(str(total_kg)),
                unit='kg',
                unit_price=0,
                line_total=0
            )
            line_items.append(line_item)
            line_number += 1
        
        return line_items
    
    @staticmethod
    def _get_pieces_per_kg(nail_size):
        """Get pieces per kg for different nail sizes"""
        # This would be configurable in the system
        nail_conversions = {
            '75x3.15': 320,  # 75mm x 3.15mm nails
            '65x2.8': 450,   # 65mm x 2.8mm nails
            '50x2.8': 580,   # 50mm x 2.8mm nails
            '40x2.8': 720,   # 40mm x 2.8mm nails
        }
        return nail_conversions.get(nail_size, 400)  # Default conversion
    
    @staticmethod
    def create_sundry_container_template(container_name, container_type, items_data):
        """Create a template sundry container with predefined items"""
        try:
            # This would be used to set up standard containers like "Bracing"
            container_template = {
                'container_name': container_name,
                'container_type': container_type,
                'items': items_data
            }
            
            return {
                'success': True,
                'template': container_template,
                'message': f'Template created for {container_name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to create template: {str(e)}'
            }
    
    @staticmethod
    def get_standard_bracing_template():
        """Get the standard bracing container template"""
        return {
            'container_name': 'Bracing',
            'container_type': 'bracing',
            'items': [
                {
                    'item_code': 'TC_BRACE_38x114',
                    'item_description': 'Top Chord Bracing - 38x114 Timber',
                    'item_category': 'timber',
                    'calculated_unit': 'm'
                },
                {
                    'item_code': 'TC_BRACE_NAILS',
                    'item_description': 'Top Chord Bracing - 75mm Galv Nails',
                    'item_category': 'nails',
                    'calculated_unit': 'ea'
                },
                {
                    'item_code': 'WEB_BRACE_38x76',
                    'item_description': 'Web Bracing - 38x76 Timber',
                    'item_category': 'timber',
                    'calculated_unit': 'm'
                },
                {
                    'item_code': 'WEB_BRACE_NAILS',
                    'item_description': 'Web Bracing - 65mm Galv Nails',
                    'item_category': 'nails',
                    'calculated_unit': 'ea'
                },
                {
                    'item_code': 'BC_BRACE_38x76',
                    'item_description': 'Bottom Chord Bracing - 38x76 Timber',
                    'item_category': 'timber',
                    'calculated_unit': 'm'
                },
                {
                    'item_code': 'BC_BRACE_NAILS',
                    'item_description': 'Bottom Chord Bracing - 65mm Galv Nails',
                    'item_category': 'nails',
                    'calculated_unit': 'ea'
                }
            ]
        }

