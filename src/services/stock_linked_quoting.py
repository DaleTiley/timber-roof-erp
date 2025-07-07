from decimal import Decimal
from typing import List, Dict, Optional
from src.models.user import db
from src.models.stock import StockItem, StockUOM, MarginGroup, DiscountGroup, CommissionGroup
from src.models.project_hierarchy import QuoteLine, Quote
from src.models.mitek_structure import MitekTruss, MitekHanger, MitekInfill
import logging

logger = logging.getLogger(__name__)

class StockLinkedQuotingService:
    """
    Service to ensure all quote/tender/order items are linked to live stock records.
    No standalone items allowed - everything must reference the master stock database.
    """
    
    @staticmethod
    def create_quote_line_from_stock(quote_id: int, stock_item_id: int, quantity: Decimal, 
                                   group_name: str = None, parent_line_id: int = None) -> QuoteLine:
        """
        Create a quote line from a stock item, ensuring all pricing comes from stock file.
        """
        try:
            # Get the stock item with all related data
            stock_item = db.session.query(StockItem).filter_by(id=stock_item_id).first()
            if not stock_item:
                raise ValueError(f"Stock item {stock_item_id} not found")
            
            # Calculate pricing from stock item
            cost_price = stock_item.cost_price or Decimal('0')
            
            # Apply margin from margin group
            margin_multiplier = Decimal('1')
            if stock_item.margin_group:
                margin_multiplier = Decimal('1') + (stock_item.margin_group.margin_percentage / Decimal('100'))
            
            # Calculate base selling price
            base_selling_price = cost_price * margin_multiplier
            
            # Apply discount from discount group
            discount_multiplier = Decimal('1')
            if stock_item.discount_group:
                discount_multiplier = Decimal('1') - (stock_item.discount_group.discount_percentage / Decimal('100'))
            
            # Final unit price
            unit_price = base_selling_price * discount_multiplier
            
            # Create quote line
            quote_line = QuoteLine(
                quote_id=quote_id,
                stock_item_id=stock_item_id,
                item_type='stock',
                stock_code=stock_item.code,
                description=stock_item.description,
                quantity=quantity,
                unit=stock_item.stock_uom.code if stock_item.stock_uom else 'ea',
                cost_price=cost_price,
                unit_price=unit_price,
                line_total=quantity * unit_price,
                group_name=group_name,
                parent_line_id=parent_line_id,
                margin_group_id=stock_item.margin_group_id,
                discount_group_id=stock_item.discount_group_id,
                commission_group_id=stock_item.commission_group_id
            )
            
            db.session.add(quote_line)
            db.session.commit()
            
            logger.info(f"Created quote line for stock item {stock_item.code}: {quantity} x {unit_price}")
            return quote_line
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create quote line from stock: {e}")
            raise
    
    @staticmethod
    def process_mitek_truss_to_stock_lines(quote_id: int, mitek_truss_data: Dict) -> List[QuoteLine]:
        """
        Process Mitek truss data and create quote lines for timber and plates from stock.
        """
        quote_lines = []
        
        try:
            # Process timber members
            for member in mitek_truss_data.get('members', []):
                timber_size = member.get('size')  # e.g., "38x114"
                length = member.get('length')     # e.g., 3000 (mm)
                quantity = member.get('quantity', 1)
                
                # Find matching timber stock item
                timber_stock = StockLinkedQuotingService._find_timber_stock_item(timber_size, length)
                if timber_stock:
                    quote_line = StockLinkedQuotingService.create_quote_line_from_stock(
                        quote_id=quote_id,
                        stock_item_id=timber_stock.id,
                        quantity=Decimal(str(quantity)),
                        group_name='roof_trusses_timber'
                    )
                    quote_lines.append(quote_line)
                else:
                    logger.warning(f"No stock item found for timber {timber_size} x {length}mm")
            
            # Process nail plates
            for plate in mitek_truss_data.get('plates', []):
                plate_code = plate.get('code')    # e.g., "M20-M8X20"
                quantity = plate.get('quantity', 1)
                
                # Find matching plate stock item
                plate_stock = StockLinkedQuotingService._find_plate_stock_item(plate_code)
                if plate_stock:
                    quote_line = StockLinkedQuotingService.create_quote_line_from_stock(
                        quote_id=quote_id,
                        stock_item_id=plate_stock.id,
                        quantity=Decimal(str(quantity)),
                        group_name='roof_trusses_plates'
                    )
                    quote_lines.append(quote_line)
                else:
                    logger.warning(f"No stock item found for plate {plate_code}")
            
            return quote_lines
            
        except Exception as e:
            logger.error(f"Failed to process Mitek truss to stock lines: {e}")
            raise
    
    @staticmethod
    def process_mitek_hangers_to_stock_lines(quote_id: int, mitek_hanger_data: List[Dict]) -> List[QuoteLine]:
        """
        Process Mitek hanger data and create quote lines from stock.
        """
        quote_lines = []
        
        try:
            for hanger in mitek_hanger_data:
                hanger_code = hanger.get('code')  # e.g., "ETH38x1MP"
                quantity = hanger.get('quantity', 1)
                
                # Find matching hanger stock item
                hanger_stock = StockLinkedQuotingService._find_hanger_stock_item(hanger_code)
                if hanger_stock:
                    quote_line = StockLinkedQuotingService.create_quote_line_from_stock(
                        quote_id=quote_id,
                        stock_item_id=hanger_stock.id,
                        quantity=Decimal(str(quantity)),
                        group_name='hangers'
                    )
                    quote_lines.append(quote_line)
                else:
                    logger.warning(f"No stock item found for hanger {hanger_code}")
            
            return quote_lines
            
        except Exception as e:
            logger.error(f"Failed to process Mitek hangers to stock lines: {e}")
            raise
    
    @staticmethod
    def apply_template_to_quote(quote_id: int, template_name: str, variables: Dict) -> List[QuoteLine]:
        """
        Apply a material template to a quote, using formulas to calculate quantities
        and linking all items to stock records.
        """
        quote_lines = []
        
        try:
            # Get template configuration
            template_config = StockLinkedQuotingService._get_template_config(template_name)
            
            for item_config in template_config.get('items', []):
                stock_code = item_config.get('stock_code')
                formula = item_config.get('formula')
                group_name = item_config.get('group_name')
                
                # Find stock item
                stock_item = db.session.query(StockItem).filter_by(code=stock_code).first()
                if not stock_item:
                    logger.warning(f"Stock item {stock_code} not found in template {template_name}")
                    continue
                
                # Calculate quantity using formula
                quantity = StockLinkedQuotingService._calculate_formula_quantity(formula, variables)
                
                # Only create line if quantity > 0
                if quantity > 0:
                    quote_line = StockLinkedQuotingService.create_quote_line_from_stock(
                        quote_id=quote_id,
                        stock_item_id=stock_item.id,
                        quantity=quantity,
                        group_name=group_name
                    )
                    quote_lines.append(quote_line)
            
            return quote_lines
            
        except Exception as e:
            logger.error(f"Failed to apply template {template_name} to quote: {e}")
            raise
    
    @staticmethod
    def update_quote_line_pricing(quote_line_id: int, new_cost: Decimal = None, 
                                new_price: Decimal = None, new_quantity: Decimal = None) -> QuoteLine:
        """
        Update quote line pricing while maintaining stock linkage.
        """
        try:
            quote_line = db.session.query(QuoteLine).filter_by(id=quote_line_id).first()
            if not quote_line:
                raise ValueError(f"Quote line {quote_line_id} not found")
            
            # Update values if provided
            if new_cost is not None:
                quote_line.cost_price = new_cost
            if new_price is not None:
                quote_line.unit_price = new_price
            if new_quantity is not None:
                quote_line.quantity = new_quantity
            
            # Recalculate line total
            quote_line.line_total = quote_line.quantity * quote_line.unit_price
            
            # Update margin percentage
            if quote_line.cost_price and quote_line.unit_price:
                quote_line.margin_percentage = ((quote_line.unit_price - quote_line.cost_price) / quote_line.unit_price) * 100
            
            db.session.commit()
            
            logger.info(f"Updated quote line {quote_line_id}: {quote_line.quantity} x {quote_line.unit_price}")
            return quote_line
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update quote line pricing: {e}")
            raise
    
    @staticmethod
    def distribute_gp_adjustment(quote_id: int, target_gp_percent: Decimal, 
                               distribution_groups: List[str]) -> Dict:
        """
        Distribute gross profit adjustment across selected groups while maintaining stock linkage.
        """
        try:
            quote = db.session.query(Quote).filter_by(id=quote_id).first()
            if not quote:
                raise ValueError(f"Quote {quote_id} not found")
            
            # Get current totals
            current_totals = StockLinkedQuotingService._calculate_quote_totals(quote_id)
            current_gp = current_totals['gross_profit_percent']
            
            # Calculate required adjustment
            target_gp = target_gp_percent
            gp_difference = target_gp - current_gp
            
            if abs(gp_difference) < Decimal('0.01'):  # Already at target
                return current_totals
            
            # Get lines in distribution groups
            distribution_lines = db.session.query(QuoteLine).filter(
                QuoteLine.quote_id == quote_id,
                QuoteLine.group_name.in_(distribution_groups),
                QuoteLine.is_header == False
            ).all()
            
            if not distribution_lines:
                raise ValueError("No lines found in specified distribution groups")
            
            # Calculate total value of distribution lines
            distribution_total = sum(line.line_total for line in distribution_lines)
            
            # Calculate required adjustment amount
            adjustment_amount = (current_totals['subtotal'] * gp_difference) / Decimal('100')
            
            # Distribute adjustment proportionally
            for line in distribution_lines:
                if distribution_total > 0:
                    line_proportion = line.line_total / distribution_total
                    line_adjustment = adjustment_amount * line_proportion
                    
                    # Adjust unit price
                    if line.quantity > 0:
                        price_adjustment = line_adjustment / line.quantity
                        line.unit_price += price_adjustment
                        line.line_total = line.quantity * line.unit_price
                        
                        # Recalculate margin
                        if line.cost_price and line.unit_price:
                            line.margin_percentage = ((line.unit_price - line.cost_price) / line.unit_price) * 100
            
            db.session.commit()
            
            # Return new totals
            new_totals = StockLinkedQuotingService._calculate_quote_totals(quote_id)
            
            logger.info(f"Distributed GP adjustment for quote {quote_id}: {current_gp:.1f}% -> {new_totals['gross_profit_percent']:.1f}%")
            return new_totals
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to distribute GP adjustment: {e}")
            raise
    
    @staticmethod
    def _find_timber_stock_item(timber_size: str, length_mm: int) -> Optional[StockItem]:
        """Find timber stock item by size and length."""
        # Look for timber with matching size and length
        # This would need to match your stock coding system
        search_pattern = f"{timber_size}x{length_mm/1000:.1f}m"
        
        return db.session.query(StockItem).filter(
            StockItem.stock_type_id.in_(
                db.session.query(StockType.id).filter(StockType.name == 'Timber')
            ),
            StockItem.code.ilike(f"%{search_pattern}%")
        ).first()
    
    @staticmethod
    def _find_plate_stock_item(plate_code: str) -> Optional[StockItem]:
        """Find nail plate stock item by code."""
        return db.session.query(StockItem).filter(
            StockItem.stock_type_id.in_(
                db.session.query(StockType.id).filter(StockType.name == 'Nail Plates')
            ),
            StockItem.code == plate_code
        ).first()
    
    @staticmethod
    def _find_hanger_stock_item(hanger_code: str) -> Optional[StockItem]:
        """Find hanger stock item by code."""
        return db.session.query(StockItem).filter(
            StockItem.stock_type_id.in_(
                db.session.query(StockType.id).filter(StockType.name == 'Hangers')
            ),
            StockItem.code == hanger_code
        ).first()
    
    @staticmethod
    def _get_template_config(template_name: str) -> Dict:
        """Get template configuration with stock codes and formulas."""
        templates = {
            'bracing': {
                'items': [
                    {
                        'stock_code': 'TIM-38x114-3.0',
                        'formula': 'ROUNDUP(({Total_Length_Eaves} / 3000), 0)',
                        'group_name': 'bracing_top_chord'
                    },
                    {
                        'stock_code': 'NAIL-75x3.15',
                        'formula': 'ROUNDUP(({Total_Length_Eaves} / 3000), 0) * 20',
                        'group_name': 'bracing_nails'
                    }
                ]
            },
            'corrugated_762': {
                'items': [
                    {
                        'stock_code': 'SHEET-0.5-AZ100-762',
                        'formula': 'ROUNDUP(({Roof_Area} / 0.762), 0)',
                        'group_name': 'sheeting'
                    },
                    {
                        'stock_code': 'SCREW-12x65-HEX',
                        'formula': 'ROUNDUP(({Roof_Area} / 0.762), 0) * 8',
                        'group_name': 'sheeting_screws'
                    }
                ]
            }
        }
        
        return templates.get(template_name, {'items': []})
    
    @staticmethod
    def _calculate_formula_quantity(formula: str, variables: Dict) -> Decimal:
        """Calculate quantity using formula and variables."""
        try:
            # Simple formula evaluation - in production, use a proper formula engine
            # Replace variables in formula
            eval_formula = formula
            for var_name, var_value in variables.items():
                eval_formula = eval_formula.replace(f'{{{var_name}}}', str(var_value))
            
            # Evaluate basic math expressions (ROUNDUP, etc.)
            # This is a simplified version - use a proper math parser in production
            if 'ROUNDUP' in eval_formula:
                import math
                # Extract the expression inside ROUNDUP
                start = eval_formula.find('ROUNDUP(') + 8
                end = eval_formula.rfind(')')
                inner_expr = eval_formula[start:end]
                
                # Split by comma to get value and decimals
                parts = inner_expr.split(',')
                if len(parts) == 2:
                    value = eval(parts[0].strip())
                    decimals = int(parts[1].strip())
                    result = math.ceil(value * (10 ** decimals)) / (10 ** decimals)
                    return Decimal(str(result))
            
            # Simple evaluation for basic expressions
            result = eval(eval_formula)
            return Decimal(str(result))
            
        except Exception as e:
            logger.error(f"Failed to calculate formula {formula}: {e}")
            return Decimal('0')
    
    @staticmethod
    def _calculate_quote_totals(quote_id: int) -> Dict:
        """Calculate quote totals."""
        lines = db.session.query(QuoteLine).filter(
            QuoteLine.quote_id == quote_id,
            QuoteLine.is_header == False
        ).all()
        
        subtotal = sum(line.line_total for line in lines)
        total_cost = sum(line.quantity * (line.cost_price or Decimal('0')) for line in lines)
        gross_profit = subtotal - total_cost
        gross_profit_percent = (gross_profit / subtotal * 100) if subtotal > 0 else Decimal('0')
        
        return {
            'subtotal': subtotal,
            'total_cost': total_cost,
            'gross_profit': gross_profit,
            'gross_profit_percent': gross_profit_percent
        }

