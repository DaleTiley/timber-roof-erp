"""
Advanced Pricing Service for ERP System
Handles complex pricing calculations, margin management, and GP distribution
"""

import math
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP


class PricingService:
    """Service for handling advanced pricing calculations and GP distribution"""
    
    def __init__(self):
        self.precision = Decimal('0.01')  # 2 decimal places for currency
        self.percentage_precision = Decimal('0.1')  # 1 decimal place for percentages
    
    def calculate_item_pricing(self, item_data: Dict) -> Dict:
        """
        Calculate all pricing fields for a single quote line item
        
        Args:
            item_data: Dictionary containing item pricing information
            
        Returns:
            Updated item data with calculated pricing fields
        """
        quantity = Decimal(str(item_data.get('quantity', 0)))
        unit_cost = Decimal(str(item_data.get('unitCost', 0)))
        margin_percent = Decimal(str(item_data.get('marginPercent', 0)))
        discount_percent = Decimal(str(item_data.get('discountPercent', 0)))
        commission_percent = Decimal(str(item_data.get('commissionPercent', 0)))
        
        # Calculate total cost
        total_cost = quantity * unit_cost
        
        # Calculate unit selling price based on margin
        margin_multiplier = Decimal('1') + (margin_percent / Decimal('100'))
        unit_selling_before_discount = unit_cost * margin_multiplier
        
        # Apply discount
        discount_multiplier = Decimal('1') - (discount_percent / Decimal('100'))
        unit_selling = unit_selling_before_discount * discount_multiplier
        
        # Calculate total selling
        total_selling = quantity * unit_selling
        
        # Calculate commission amount
        commission_amount = total_selling * (commission_percent / Decimal('100'))
        
        # Calculate net selling (after commission)
        net_selling = total_selling - commission_amount
        
        # Calculate actual margin achieved
        if unit_cost > 0:
            actual_margin_percent = ((unit_selling - unit_cost) / unit_cost) * Decimal('100')
        else:
            actual_margin_percent = Decimal('0')
        
        # Update item data
        item_data.update({
            'totalCost': float(total_cost.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'unitSelling': float(unit_selling.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'totalSelling': float(total_selling.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'commissionAmount': float(commission_amount.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'netSelling': float(net_selling.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'actualMarginPercent': float(actual_margin_percent.quantize(self.percentage_precision, rounding=ROUND_HALF_UP))
        })
        
        return item_data
    
    def calculate_group_totals(self, group_data: Dict) -> Dict:
        """
        Calculate totals for a quote group
        
        Args:
            group_data: Dictionary containing group information and items
            
        Returns:
            Updated group data with calculated totals
        """
        items = group_data.get('items', [])
        
        total_cost = Decimal('0')
        total_selling = Decimal('0')
        total_commission = Decimal('0')
        total_net_selling = Decimal('0')
        
        for item in items:
            # Ensure item pricing is calculated
            item = self.calculate_item_pricing(item)
            
            total_cost += Decimal(str(item.get('totalCost', 0)))
            total_selling += Decimal(str(item.get('totalSelling', 0)))
            total_commission += Decimal(str(item.get('commissionAmount', 0)))
            total_net_selling += Decimal(str(item.get('netSelling', 0)))
        
        # Calculate group margin
        if total_cost > 0:
            group_margin_percent = ((total_selling - total_cost) / total_cost) * Decimal('100')
        else:
            group_margin_percent = Decimal('0')
        
        # Calculate group GP percentage
        if total_selling > 0:
            group_gp_percent = ((total_selling - total_cost) / total_selling) * Decimal('100')
        else:
            group_gp_percent = Decimal('0')
        
        group_data.update({
            'totalCost': float(total_cost.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'totalSelling': float(total_selling.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'totalCommission': float(total_commission.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'totalNetSelling': float(total_net_selling.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'marginPercent': float(group_margin_percent.quantize(self.percentage_precision, rounding=ROUND_HALF_UP)),
            'gpPercent': float(group_gp_percent.quantize(self.percentage_precision, rounding=ROUND_HALF_UP))
        })
        
        return group_data
    
    def calculate_quote_totals(self, quote_data: Dict) -> Dict:
        """
        Calculate totals for entire quote
        
        Args:
            quote_data: Dictionary containing quote information and groups
            
        Returns:
            Updated quote data with calculated totals
        """
        groups = quote_data.get('groups', [])
        
        total_cost = Decimal('0')
        total_selling = Decimal('0')
        total_commission = Decimal('0')
        total_net_selling = Decimal('0')
        
        for group in groups:
            # Ensure group totals are calculated
            group = self.calculate_group_totals(group)
            
            total_cost += Decimal(str(group.get('totalCost', 0)))
            total_selling += Decimal(str(group.get('totalSelling', 0)))
            total_commission += Decimal(str(group.get('totalCommission', 0)))
            total_net_selling += Decimal(str(group.get('totalNetSelling', 0)))
        
        # Calculate quote-level metrics
        gross_profit = total_selling - total_cost
        
        if total_selling > 0:
            gross_profit_percent = (gross_profit / total_selling) * Decimal('100')
        else:
            gross_profit_percent = Decimal('0')
        
        if total_cost > 0:
            markup_percent = (gross_profit / total_cost) * Decimal('100')
        else:
            markup_percent = Decimal('0')
        
        quote_data.update({
            'totalCost': float(total_cost.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'totalSelling': float(total_selling.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'totalCommission': float(total_commission.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'totalNetSelling': float(total_net_selling.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'grossProfit': float(gross_profit.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'grossProfitPercent': float(gross_profit_percent.quantize(self.percentage_precision, rounding=ROUND_HALF_UP)),
            'markupPercent': float(markup_percent.quantize(self.percentage_precision, rounding=ROUND_HALF_UP))
        })
        
        return quote_data
    
    def distribute_gp_adjustment(self, quote_data: Dict, target_gp_percent: float, 
                                selected_group_ids: List[str]) -> Dict:
        """
        Distribute GP adjustment across selected groups
        
        Args:
            quote_data: Current quote data
            target_gp_percent: Target gross profit percentage
            selected_group_ids: List of group IDs to distribute adjustment to
            
        Returns:
            Updated quote data with adjusted pricing
        """
        if not selected_group_ids:
            return quote_data
        
        # Calculate current totals
        quote_data = self.calculate_quote_totals(quote_data)
        
        current_total_cost = Decimal(str(quote_data['totalCost']))
        current_total_selling = Decimal(str(quote_data['totalSelling']))
        target_gp = Decimal(str(target_gp_percent))
        
        # Calculate required selling total for target GP
        if target_gp >= Decimal('100'):
            raise ValueError("Target GP percentage cannot be 100% or higher")
        
        target_total_selling = current_total_cost / (Decimal('1') - (target_gp / Decimal('100')))
        adjustment_amount = target_total_selling - current_total_selling
        
        # Get selected groups and their current selling totals
        selected_groups = [g for g in quote_data['groups'] if g['id'] in selected_group_ids]
        selected_total_selling = sum(Decimal(str(g.get('totalSelling', 0))) for g in selected_groups)
        
        if selected_total_selling == 0:
            return quote_data
        
        # Distribute adjustment proportionally across selected groups
        for group in quote_data['groups']:
            if group['id'] in selected_group_ids:
                group_selling = Decimal(str(group.get('totalSelling', 0)))
                group_proportion = group_selling / selected_total_selling
                group_adjustment = adjustment_amount * group_proportion
                
                # Distribute group adjustment across items proportionally
                group_items = group.get('items', [])
                group_items_selling = sum(Decimal(str(item.get('totalSelling', 0))) for item in group_items)
                
                if group_items_selling > 0:
                    for item in group_items:
                        item_selling = Decimal(str(item.get('totalSelling', 0)))
                        item_proportion = item_selling / group_items_selling
                        item_adjustment = group_adjustment * item_proportion
                        
                        # Update item selling price
                        new_total_selling = item_selling + item_adjustment
                        quantity = Decimal(str(item.get('quantity', 1)))
                        new_unit_selling = new_total_selling / quantity if quantity > 0 else Decimal('0')
                        
                        item['totalSelling'] = float(new_total_selling.quantize(self.precision, rounding=ROUND_HALF_UP))
                        item['unitSelling'] = float(new_unit_selling.quantize(self.precision, rounding=ROUND_HALF_UP))
                        
                        # Recalculate margin based on new selling price
                        unit_cost = Decimal(str(item.get('unitCost', 0)))
                        if unit_cost > 0:
                            new_margin_percent = ((new_unit_selling - unit_cost) / unit_cost) * Decimal('100')
                            item['marginPercent'] = float(new_margin_percent.quantize(self.percentage_precision, rounding=ROUND_HALF_UP))
                        
                        # Recalculate other pricing fields
                        item = self.calculate_item_pricing(item)
        
        # Recalculate all totals
        quote_data = self.calculate_quote_totals(quote_data)
        
        return quote_data
    
    def apply_bulk_margin_adjustment(self, quote_data: Dict, group_id: str, 
                                   new_margin_percent: float) -> Dict:
        """
        Apply bulk margin adjustment to all items in a group
        
        Args:
            quote_data: Current quote data
            group_id: ID of the group to adjust
            new_margin_percent: New margin percentage to apply
            
        Returns:
            Updated quote data with adjusted margins
        """
        for group in quote_data['groups']:
            if group['id'] == group_id:
                for item in group.get('items', []):
                    item['marginPercent'] = new_margin_percent
                    item = self.calculate_item_pricing(item)
                break
        
        # Recalculate all totals
        quote_data = self.calculate_quote_totals(quote_data)
        
        return quote_data
    
    def apply_bulk_discount_adjustment(self, quote_data: Dict, group_id: str, 
                                     discount_percent: float) -> Dict:
        """
        Apply bulk discount adjustment to all items in a group
        
        Args:
            quote_data: Current quote data
            group_id: ID of the group to adjust
            discount_percent: Discount percentage to apply
            
        Returns:
            Updated quote data with adjusted discounts
        """
        for group in quote_data['groups']:
            if group['id'] == group_id:
                for item in group.get('items', []):
                    item['discountPercent'] = discount_percent
                    item = self.calculate_item_pricing(item)
                break
        
        # Recalculate all totals
        quote_data = self.calculate_quote_totals(quote_data)
        
        return quote_data
    
    def calculate_waste_factor(self, base_quantity: float, waste_percent: float) -> float:
        """
        Calculate quantity including waste factor
        
        Args:
            base_quantity: Base quantity before waste
            waste_percent: Waste percentage to add
            
        Returns:
            Quantity including waste factor
        """
        base_qty = Decimal(str(base_quantity))
        waste_pct = Decimal(str(waste_percent))
        
        waste_multiplier = Decimal('1') + (waste_pct / Decimal('100'))
        final_quantity = base_qty * waste_multiplier
        
        return float(final_quantity.quantize(self.precision, rounding=ROUND_HALF_UP))
    
    def round_up_to_stock_length(self, required_length: float, stock_lengths: List[float]) -> Tuple[float, int]:
        """
        Round up required length to next available stock length and calculate quantity needed
        
        Args:
            required_length: Total length required
            stock_lengths: Available stock lengths (sorted ascending)
            
        Returns:
            Tuple of (selected_stock_length, quantity_needed)
        """
        if not stock_lengths:
            return required_length, 1
        
        # Sort stock lengths to ensure we get the most efficient option
        sorted_lengths = sorted(stock_lengths)
        
        # Find the most efficient stock length (minimize waste)
        best_length = None
        best_quantity = float('inf')
        best_waste = float('inf')
        
        for stock_length in sorted_lengths:
            if stock_length > 0:
                quantity_needed = math.ceil(required_length / stock_length)
                total_supplied = quantity_needed * stock_length
                waste = total_supplied - required_length
                waste_percent = (waste / total_supplied) * 100 if total_supplied > 0 else 0
                
                # Prefer options with less waste, but also consider quantity efficiency
                if waste_percent < best_waste or (waste_percent == best_waste and quantity_needed < best_quantity):
                    best_length = stock_length
                    best_quantity = quantity_needed
                    best_waste = waste_percent
        
        return best_length or sorted_lengths[0], int(best_quantity)
    
    def calculate_composite_item_pricing(self, composite_recipe: Dict) -> Dict:
        """
        Calculate pricing for composite items (tender rates)
        
        Args:
            composite_recipe: Dictionary containing recipe components and markup
            
        Returns:
            Calculated composite item pricing
        """
        components = composite_recipe.get('components', [])
        markup_percent = Decimal(str(composite_recipe.get('markupPercent', 0)))
        overhead_percent = Decimal(str(composite_recipe.get('overheadPercent', 0)))
        
        total_material_cost = Decimal('0')
        total_labour_cost = Decimal('0')
        total_transport_cost = Decimal('0')
        total_overhead_cost = Decimal('0')
        
        for component in components:
            component_cost = Decimal(str(component.get('totalCost', 0)))
            component_type = component.get('type', 'material')
            
            if component_type == 'material':
                total_material_cost += component_cost
            elif component_type == 'labour':
                total_labour_cost += component_cost
            elif component_type == 'transport':
                total_transport_cost += component_cost
            elif component_type == 'overhead':
                total_overhead_cost += component_cost
        
        # Calculate base cost
        base_cost = total_material_cost + total_labour_cost + total_transport_cost
        
        # Add overhead
        overhead_amount = base_cost * (overhead_percent / Decimal('100'))
        total_cost = base_cost + overhead_amount + total_overhead_cost
        
        # Apply markup
        markup_amount = total_cost * (markup_percent / Decimal('100'))
        selling_price = total_cost + markup_amount
        
        return {
            'materialCost': float(total_material_cost.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'labourCost': float(total_labour_cost.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'transportCost': float(total_transport_cost.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'overheadCost': float(total_overhead_cost.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'overheadAmount': float(overhead_amount.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'totalCost': float(total_cost.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'markupAmount': float(markup_amount.quantize(self.precision, rounding=ROUND_HALF_UP)),
            'sellingPrice': float(selling_price.quantize(self.precision, rounding=ROUND_HALF_UP))
        }


# Global instance for use across the application
pricing_service = PricingService()

