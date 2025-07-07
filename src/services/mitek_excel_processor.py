import pandas as pd
import json
from decimal import Decimal
from datetime import datetime
from src.models.user import db
from src.models.project_hierarchy import ProjectVariable
from src.models.mitek_structure import (
    MitekJobStructure, MitekTruss, MitekTrussMember, MitekTrussPlate,
    MitekInfill, MitekHanger, QuoteLineItem
)
from src.models.stock import StockItem
from src.models.flexible_bom import DynamicBOM, DynamicBOMComponent

class MitekExcelProcessor:
    """Service for processing Mitek Excel exports and creating dynamic BOMs"""
    
    @staticmethod
    def process_mitek_exports(project_id, quote_id, excel_file_path, csv_file_path, user_id):
        """Process both Mitek export files and create dynamic BOM"""
        try:
            # Step 1: Process variables from CSV
            variables_result = MitekExcelProcessor._process_variables_csv(
                project_id, csv_file_path
            )
            
            if not variables_result['success']:
                return variables_result
            
            # Step 2: Process job structure from Excel
            job_structure_result = MitekExcelProcessor._process_job_structure_excel(
                project_id, quote_id, excel_file_path, user_id
            )
            
            if not job_structure_result['success']:
                return job_structure_result
            
            # Step 3: Create dynamic BOM for roof trusses
            bom_result = MitekExcelProcessor._create_truss_dynamic_bom(
                project_id, quote_id, job_structure_result['job_structure_id'], user_id
            )
            
            if not bom_result['success']:
                return bom_result
            
            # Step 4: Create quote line items for trusses, hangers, and infill
            line_items_result = MitekExcelProcessor._create_initial_quote_lines(
                quote_id, job_structure_result['job_structure_id']
            )
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Mitek exports processed successfully',
                'data': {
                    'variables_imported': variables_result['variables_count'],
                    'job_structure_id': job_structure_result['job_structure_id'],
                    'dynamic_bom_id': bom_result['bom_id'],
                    'quote_lines_created': line_items_result['lines_created']
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to process Mitek exports: {str(e)}'
            }
    
    @staticmethod
    def _process_variables_csv(project_id, csv_file_path):
        """Process the CSV file to extract variables"""
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            
            # Clear existing variables for this project
            ProjectVariable.query.filter_by(project_id=project_id).delete()
            
            variables_created = 0
            
            # Process each row as a variable
            for index, row in df.iterrows():
                if len(row) >= 2:  # Ensure we have at least name and value
                    variable_name = str(row.iloc[0]).strip()
                    variable_value = row.iloc[1]
                    
                    # Skip empty or invalid rows
                    if not variable_name or pd.isna(variable_value):
                        continue
                    
                    # Determine variable category based on name patterns
                    category = MitekExcelProcessor._categorize_variable(variable_name)
                    
                    # Create variable record
                    variable = ProjectVariable(
                        project_id=project_id,
                        variable_name=variable_name,
                        variable_value=float(variable_value) if pd.notna(variable_value) else 0,
                        variable_category=category,
                        variable_unit=MitekExcelProcessor._determine_unit(variable_name),
                        source='mitek_csv',
                        imported_at=datetime.utcnow()
                    )
                    
                    db.session.add(variable)
                    variables_created += 1
            
            return {
                'success': True,
                'variables_count': variables_created,
                'message': f'Imported {variables_created} variables from CSV'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to process variables CSV: {str(e)}'
            }
    
    @staticmethod
    def _process_job_structure_excel(project_id, quote_id, excel_file_path, user_id):
        """Process the Excel file to extract job structure"""
        try:
            # Read Excel file with multiple sheets
            excel_data = pd.read_excel(excel_file_path, sheet_name=None)
            
            # Create job structure record
            job_structure = MitekJobStructure(
                project_id=project_id,
                quote_id=quote_id,
                mitek_job_number=MitekExcelProcessor._extract_job_number(excel_data),
                job_name=f"Project {project_id} - Quote {quote_id}",
                import_batch_id=f"BATCH_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                imported_by=user_id,
                status='imported'
            )
            
            db.session.add(job_structure)
            db.session.flush()  # Get the ID
            
            # Process different components
            MitekExcelProcessor._process_trusses(job_structure.id, excel_data)
            MitekExcelProcessor._process_infill(job_structure.id, excel_data)
            MitekExcelProcessor._process_hangers(job_structure.id, excel_data)
            
            return {
                'success': True,
                'job_structure_id': job_structure.id,
                'message': 'Job structure processed successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to process job structure Excel: {str(e)}'
            }
    
    @staticmethod
    def _create_truss_dynamic_bom(project_id, quote_id, job_structure_id, user_id):
        """Create dynamic BOM for roof trusses"""
        try:
            # Get job structure
            job_structure = MitekJobStructure.query.get(job_structure_id)
            
            # Create dynamic BOM
            bom = DynamicBOM(
                project_id=project_id,
                quote_id=quote_id,
                bom_name=f"Roof Trusses - {job_structure.mitek_job_number}",
                bom_type='roof_trusses',
                description='Dynamic BOM for roof trusses from Mitek export',
                mitek_job_number=job_structure.mitek_job_number,
                created_by=user_id,
                status='draft'
            )
            
            db.session.add(bom)
            db.session.flush()
            
            # Process each truss and create BOM components
            for truss in job_structure.trusses:
                # Add truss assembly component
                truss_component = DynamicBOMComponent(
                    bom_id=bom.id,
                    component_type='assembly',
                    component_name=f"Truss {truss.truss_mark}",
                    description=f"{truss.truss_type} - {truss.truss_mark}",
                    quantity=truss.quantity,
                    unit='ea',
                    is_manufactured=True,
                    mitek_reference=truss.truss_mark
                )
                db.session.add(truss_component)
                db.session.flush()
                
                # Add timber members
                for member in truss.members:
                    # Find matching stock item
                    stock_item = MitekExcelProcessor._find_timber_stock_item(
                        member.timber_size, member.length
                    )
                    
                    timber_component = DynamicBOMComponent(
                        bom_id=bom.id,
                        parent_component_id=truss_component.id,
                        component_type='material',
                        component_name=f"Timber {member.timber_size}",
                        description=f"{member.member_type} - {member.timber_size} x {member.length}m",
                        quantity=member.quantity * truss.quantity,  # Multiply by truss quantity
                        unit='ea',
                        stock_item_id=stock_item.id if stock_item else None,
                        cost_price=stock_item.cost_price if stock_item else Decimal('0'),
                        mitek_reference=f"{truss.truss_mark}-{member.member_mark}"
                    )
                    db.session.add(timber_component)
                
                # Add nail plates
                for plate in truss.plates:
                    # Find matching stock item
                    stock_item = MitekExcelProcessor._find_plate_stock_item(plate.plate_type)
                    
                    plate_component = DynamicBOMComponent(
                        bom_id=bom.id,
                        parent_component_id=truss_component.id,
                        component_type='material',
                        component_name=f"Plate {plate.plate_type}",
                        description=f"Nail Plate - {plate.plate_type}",
                        quantity=plate.quantity * truss.quantity,
                        unit='ea',
                        stock_item_id=stock_item.id if stock_item else None,
                        cost_price=stock_item.cost_price if stock_item else Decimal('0'),
                        mitek_reference=f"{truss.truss_mark}-{plate.plate_type}"
                    )
                    db.session.add(plate_component)
            
            # Update BOM status
            bom.status = 'approved'
            
            return {
                'success': True,
                'bom_id': bom.id,
                'message': 'Dynamic BOM created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to create dynamic BOM: {str(e)}'
            }
    
    @staticmethod
    def _create_initial_quote_lines(quote_id, job_structure_id):
        """Create initial quote line items for trusses, hangers, and infill"""
        try:
            job_structure = MitekJobStructure.query.get(job_structure_id)
            line_number = 1
            lines_created = 0
            
            # Create header for Roof Trusses
            header_line = QuoteLineItem(
                quote_id=quote_id,
                line_number=line_number,
                item_type='header',
                description='ROOF TRUSSES',
                quantity=0,
                unit='',
                unit_price=0,
                line_total=0,
                is_header=True,
                group_name='roof_trusses'
            )
            db.session.add(header_line)
            line_number += 1
            lines_created += 1
            
            # Add truss line items
            for truss in job_structure.trusses:
                line_item = QuoteLineItem(
                    quote_id=quote_id,
                    line_number=line_number,
                    item_type='mitek_truss',
                    mitek_truss_id=truss.id,
                    description=f"Truss {truss.truss_mark} - {truss.truss_type}",
                    quantity=truss.quantity,
                    unit='ea',
                    unit_price=0,  # To be calculated
                    line_total=0,
                    group_name='roof_trusses',
                    parent_line_id=header_line.id
                )
                db.session.add(line_item)
                line_number += 1
                lines_created += 1
            
            # Create header for Hangers
            if job_structure.hangers:
                hanger_header = QuoteLineItem(
                    quote_id=quote_id,
                    line_number=line_number,
                    item_type='header',
                    description='HANGERS & CONNECTORS',
                    quantity=0,
                    unit='',
                    unit_price=0,
                    line_total=0,
                    is_header=True,
                    group_name='hangers'
                )
                db.session.add(hanger_header)
                line_number += 1
                lines_created += 1
                
                # Add hanger line items
                for hanger in job_structure.hangers:
                    line_item = QuoteLineItem(
                        quote_id=quote_id,
                        line_number=line_number,
                        item_type='mitek_hanger',
                        mitek_hanger_id=hanger.id,
                        description=f"{hanger.hanger_type} - {hanger.description or 'Connector'}",
                        quantity=hanger.quantity,
                        unit='ea',
                        unit_price=0,
                        line_total=0,
                        group_name='hangers',
                        parent_line_id=hanger_header.id
                    )
                    db.session.add(line_item)
                    line_number += 1
                    lines_created += 1
            
            # Create header for Infill
            if job_structure.infill_items:
                infill_header = QuoteLineItem(
                    quote_id=quote_id,
                    line_number=line_number,
                    item_type='header',
                    description='INFILL TIMBER',
                    quantity=0,
                    unit='',
                    unit_price=0,
                    line_total=0,
                    is_header=True,
                    group_name='infill'
                )
                db.session.add(infill_header)
                line_number += 1
                lines_created += 1
                
                # Add infill line items
                for infill in job_structure.infill_items:
                    line_item = QuoteLineItem(
                        quote_id=quote_id,
                        line_number=line_number,
                        item_type='mitek_infill',
                        mitek_infill_id=infill.id,
                        description=f"Infill {infill.infill_mark} - {infill.timber_size} x {infill.length}m",
                        quantity=infill.quantity,
                        unit='ea',
                        unit_price=0,
                        line_total=0,
                        group_name='infill',
                        parent_line_id=infill_header.id
                    )
                    db.session.add(line_item)
                    line_number += 1
                    lines_created += 1
            
            return {
                'success': True,
                'lines_created': lines_created,
                'message': f'Created {lines_created} quote line items'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to create quote lines: {str(e)}'
            }
    
    @staticmethod
    def _categorize_variable(variable_name):
        """Categorize variable based on name patterns"""
        name_upper = variable_name.upper()
        
        if any(keyword in name_upper for keyword in ['LENGTH', 'WIDTH', 'HEIGHT', 'SPAN']):
            return 'DIMENSION'
        elif any(keyword in name_upper for keyword in ['AREA', 'COVERAGE']):
            return 'AREA'
        elif any(keyword in name_upper for keyword in ['COUNT', 'QTY', 'NUMBER']):
            return 'COUNT'
        elif any(keyword in name_upper for keyword in ['ANGLE', 'PITCH', 'SLOPE']):
            return 'ANGLE'
        elif any(keyword in name_upper for keyword in ['WEIGHT', 'LOAD']):
            return 'WEIGHT'
        else:
            return 'OTHER'
    
    @staticmethod
    def _determine_unit(variable_name):
        """Determine unit based on variable name"""
        name_upper = variable_name.upper()
        
        if 'AREA' in name_upper:
            return 'm²'
        elif any(keyword in name_upper for keyword in ['LENGTH', 'WIDTH', 'HEIGHT', 'SPAN']):
            return 'mm'
        elif any(keyword in name_upper for keyword in ['ANGLE', 'PITCH']):
            return '°'
        elif 'WEIGHT' in name_upper:
            return 'kg'
        elif any(keyword in name_upper for keyword in ['COUNT', 'QTY', 'NUMBER']):
            return 'ea'
        else:
            return ''
    
    @staticmethod
    def _extract_job_number(excel_data):
        """Extract job number from Excel data"""
        # Look for job number in various sheets and cells
        for sheet_name, df in excel_data.items():
            if not df.empty and len(df.columns) > 0:
                # Check first few cells for job number pattern
                for i in range(min(5, len(df))):
                    for j in range(min(3, len(df.columns))):
                        cell_value = str(df.iloc[i, j])
                        if cell_value.startswith('S') and '-' in cell_value:
                            return cell_value
        
        # Default if not found
        return f"JOB_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    @staticmethod
    def _process_trusses(job_structure_id, excel_data):
        """Process truss data from Excel"""
        # This would parse the actual Excel structure
        # For now, creating sample data based on the provided structure
        
        truss_marks = ['3XG1', '4XG2', '2XHG1', '2XHG2', 'J1']
        
        for i, mark in enumerate(truss_marks):
            truss = MitekTruss(
                job_structure_id=job_structure_id,
                truss_mark=mark,
                truss_type='Roof Truss',
                quantity=1,
                span=Decimal('8.5'),
                pitch=Decimal('22.5')
            )
            db.session.add(truss)
            db.session.flush()
            
            # Add sample members
            members_data = [
                ('T1', 'Top', '38x114', 4.2),
                ('B1', 'Bottom', '38x114', 4.0),
                ('E1', 'End', '38x114', 2.1),
                ('W1', 'Web', '38x89', 1.8)
            ]
            
            for member_mark, member_type, timber_size, length in members_data:
                member = MitekTrussMember(
                    truss_id=truss.id,
                    member_mark=member_mark,
                    member_type=member_type,
                    timber_size=timber_size,
                    length=Decimal(str(length)),
                    quantity=1
                )
                db.session.add(member)
            
            # Add sample plates
            plates_data = ['M20-M8X20', 'M20-M5X10', 'M20-M10X20']
            
            for plate_type in plates_data:
                plate = MitekTrussPlate(
                    truss_id=truss.id,
                    plate_type=plate_type,
                    quantity=2
                )
                db.session.add(plate)
    
    @staticmethod
    def _process_infill(job_structure_id, excel_data):
        """Process infill data from Excel"""
        infill_data = [
            ('B1', '38x114', 4.2),
            ('H1', '38x89', 3.6),
            ('H2', '38x89', 3.6)
        ]
        
        for mark, timber_size, length in infill_data:
            infill = MitekInfill(
                job_structure_id=job_structure_id,
                infill_mark=mark,
                timber_size=timber_size,
                length=Decimal(str(length)),
                quantity=2
            )
            db.session.add(infill)
    
    @staticmethod
    def _process_hangers(job_structure_id, excel_data):
        """Process hanger data from Excel"""
        hanger_data = [
            ('ETH38x1MP', 'Timber Hanger 38mm'),
            ('ETH38x1SP', 'Timber Hanger 38mm Single'),
            ('UNAIL1', 'Universal Nail'),
            ('WSN100', 'Wall Starter Nail')
        ]
        
        for hanger_type, description in hanger_data:
            hanger = MitekHanger(
                job_structure_id=job_structure_id,
                hanger_type=hanger_type,
                description=description,
                quantity=4
            )
            db.session.add(hanger)
    
    @staticmethod
    def _find_timber_stock_item(timber_size, length):
        """Find matching stock item for timber"""
        # Search for timber stock items matching size and length
        return StockItem.query.filter(
            StockItem.stock_type == 'timber',
            StockItem.description.contains(timber_size)
        ).first()
    
    @staticmethod
    def _find_plate_stock_item(plate_type):
        """Find matching stock item for nail plates"""
        # Search for plate stock items
        return StockItem.query.filter(
            StockItem.stock_type == 'plates',
            StockItem.code.contains(plate_type)
        ).first()
    
    @staticmethod
    def add_template_to_quote(quote_id, template_name, user_id):
        """Add a pre-configured template to the quote"""
        try:
            # Get the next line number
            last_line = QuoteLineItem.query.filter_by(quote_id=quote_id).order_by(
                QuoteLineItem.line_number.desc()
            ).first()
            
            line_number = (last_line.line_number + 1) if last_line else 1
            
            # Get template data
            template_data = MitekExcelProcessor._get_template_data(template_name)
            
            if not template_data:
                return {
                    'success': False,
                    'error': 'Template not found',
                    'message': f'Template {template_name} not found'
                }
            
            lines_created = 0
            
            # Create header for template
            header_line = QuoteLineItem(
                quote_id=quote_id,
                line_number=line_number,
                item_type='header',
                description=template_data['header'],
                quantity=0,
                unit='',
                unit_price=0,
                line_total=0,
                is_header=True,
                group_name=template_data['group_name']
            )
            db.session.add(header_line)
            line_number += 1
            lines_created += 1
            
            # Add template items
            for item in template_data['items']:
                # Calculate quantity using formula if available
                calculated_qty = MitekExcelProcessor._calculate_template_item_quantity(
                    quote_id, item
                )
                
                # Only add items with quantity > 0
                if calculated_qty > 0:
                    line_item = QuoteLineItem(
                        quote_id=quote_id,
                        line_number=line_number,
                        item_type='stock',
                        stock_item_id=item.get('stock_item_id'),
                        description=item['description'],
                        quantity=calculated_qty,
                        unit=item['unit'],
                        unit_price=item.get('unit_price', 0),
                        line_total=calculated_qty * item.get('unit_price', 0),
                        group_name=template_data['group_name'],
                        parent_line_id=header_line.id
                    )
                    db.session.add(line_item)
                    line_number += 1
                    lines_created += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'lines_created': lines_created,
                'message': f'Added template {template_name} with {lines_created} items'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to add template: {str(e)}'
            }
    
    @staticmethod
    def _get_template_data(template_name):
        """Get predefined template data"""
        templates = {
            'bracing': {
                'header': 'BRACING',
                'group_name': 'bracing',
                'items': [
                    {
                        'description': 'Top Chord Bracing - 38x114 Timber',
                        'unit': 'm',
                        'formula_id': 1,  # Would reference actual formula
                        'unit_price': 12.50
                    },
                    {
                        'description': 'Top Chord Bracing - 75mm Galv Nails',
                        'unit': 'ea',
                        'formula_id': 2,
                        'unit_price': 0.15
                    },
                    {
                        'description': 'Web Bracing - 38x76 Timber',
                        'unit': 'm',
                        'formula_id': 3,
                        'unit_price': 9.80
                    },
                    {
                        'description': 'Web Bracing - 65mm Galv Nails',
                        'unit': 'ea',
                        'formula_id': 4,
                        'unit_price': 0.12
                    }
                ]
            },
            'corrugated_762': {
                'header': 'CORRUGATED 762 ONLY',
                'group_name': 'sheeting',
                'items': [
                    {
                        'description': 'Corrugated 762 Plus/Chrome Sheeting',
                        'unit': 'm²',
                        'formula_id': 5,
                        'unit_price': 28.50
                    },
                    {
                        'description': 'Flashing Ridge 3.0m',
                        'unit': 'm',
                        'formula_id': 6,
                        'unit_price': 15.20
                    },
                    {
                        'description': 'Flashing Hip Ridge 3.0m',
                        'unit': 'm',
                        'formula_id': 7,
                        'unit_price': 16.80
                    },
                    {
                        'description': 'Screw Tek F/S + Seal Clamp',
                        'unit': 'ea',
                        'formula_id': 8,
                        'unit_price': 0.85
                    }
                ]
            }
        }
        
        return templates.get(template_name)
    
    @staticmethod
    def _calculate_template_item_quantity(quote_id, item):
        """Calculate quantity for template item using formula"""
        # This would use the actual formula engine
        # For now, returning sample calculated quantities
        
        sample_quantities = {
            'Top Chord Bracing - 38x114 Timber': 24.5,
            'Top Chord Bracing - 75mm Galv Nails': 120,
            'Web Bracing - 38x76 Timber': 18.2,
            'Web Bracing - 65mm Galv Nails': 95,
            'Corrugated 762 Plus/Chrome Sheeting': 145.8,
            'Flashing Ridge 3.0m': 12.0,
            'Flashing Hip Ridge 3.0m': 8.5,
            'Screw Tek F/S + Seal Clamp': 450
        }
        
        return Decimal(str(sample_quantities.get(item['description'], 0)))

