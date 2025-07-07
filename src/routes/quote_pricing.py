"""
Quote Pricing API Routes
Handles advanced pricing calculations and GP distribution
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import logging
from typing import Dict, List

from ..services.pricing_service import pricing_service

# Create blueprint
quote_pricing_bp = Blueprint('quote_pricing', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@quote_pricing_bp.route('/api/quotes/<quote_id>/calculate', methods=['POST'])
@cross_origin()
def calculate_quote_pricing(quote_id):
    """
    Calculate all pricing for a quote including items, groups, and totals
    """
    try:
        quote_data = request.get_json()
        
        if not quote_data:
            return jsonify({'error': 'No quote data provided'}), 400
        
        # Calculate pricing for all items and groups
        calculated_quote = pricing_service.calculate_quote_totals(quote_data)
        
        logger.info(f"Calculated pricing for quote {quote_id}")
        
        return jsonify({
            'success': True,
            'quote': calculated_quote
        })
        
    except Exception as e:
        logger.error(f"Error calculating quote pricing: {str(e)}")
        return jsonify({'error': str(e)}), 500


@quote_pricing_bp.route('/api/quotes/<quote_id>/items/<item_id>/update', methods=['PUT'])
@cross_origin()
def update_quote_item(quote_id, item_id):
    """
    Update a specific quote item and recalculate pricing
    """
    try:
        update_data = request.get_json()
        
        if not update_data:
            return jsonify({'error': 'No update data provided'}), 400
        
        # Get the item data
        item_data = update_data.get('item', {})
        quote_data = update_data.get('quote', {})
        
        # Calculate item pricing
        calculated_item = pricing_service.calculate_item_pricing(item_data)
        
        # If full quote data provided, recalculate totals
        if quote_data:
            # Update the item in the quote
            for group in quote_data.get('groups', []):
                for item in group.get('items', []):
                    if item.get('id') == item_id:
                        item.update(calculated_item)
                        break
            
            # Recalculate quote totals
            calculated_quote = pricing_service.calculate_quote_totals(quote_data)
            
            return jsonify({
                'success': True,
                'item': calculated_item,
                'quote': calculated_quote
            })
        
        return jsonify({
            'success': True,
            'item': calculated_item
        })
        
    except Exception as e:
        logger.error(f"Error updating quote item: {str(e)}")
        return jsonify({'error': str(e)}), 500


@quote_pricing_bp.route('/api/quotes/<quote_id>/gp-distribution', methods=['POST'])
@cross_origin()
def distribute_gp_adjustment(quote_id):
    """
    Distribute GP adjustment across selected groups
    """
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({'error': 'No request data provided'}), 400
        
        quote_data = request_data.get('quote', {})
        target_gp_percent = request_data.get('targetGpPercent')
        selected_group_ids = request_data.get('selectedGroupIds', [])
        
        if target_gp_percent is None:
            return jsonify({'error': 'Target GP percentage is required'}), 400
        
        if not selected_group_ids:
            return jsonify({'error': 'At least one group must be selected'}), 400
        
        # Validate target GP percentage
        if target_gp_percent < 0 or target_gp_percent >= 100:
            return jsonify({'error': 'Target GP percentage must be between 0 and 99.9'}), 400
        
        # Distribute GP adjustment
        adjusted_quote = pricing_service.distribute_gp_adjustment(
            quote_data, target_gp_percent, selected_group_ids
        )
        
        logger.info(f"Distributed GP adjustment for quote {quote_id} to {target_gp_percent}%")
        
        return jsonify({
            'success': True,
            'quote': adjusted_quote,
            'message': f'GP adjusted to {target_gp_percent}% across selected groups'
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error distributing GP adjustment: {str(e)}")
        return jsonify({'error': str(e)}), 500


@quote_pricing_bp.route('/api/quotes/<quote_id>/groups/<group_id>/bulk-margin', methods=['PUT'])
@cross_origin()
def apply_bulk_margin(quote_id, group_id):
    """
    Apply bulk margin adjustment to all items in a group
    """
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({'error': 'No request data provided'}), 400
        
        quote_data = request_data.get('quote', {})
        new_margin_percent = request_data.get('marginPercent')
        
        if new_margin_percent is None:
            return jsonify({'error': 'Margin percentage is required'}), 400
        
        # Apply bulk margin adjustment
        adjusted_quote = pricing_service.apply_bulk_margin_adjustment(
            quote_data, group_id, new_margin_percent
        )
        
        logger.info(f"Applied bulk margin {new_margin_percent}% to group {group_id} in quote {quote_id}")
        
        return jsonify({
            'success': True,
            'quote': adjusted_quote,
            'message': f'Margin adjusted to {new_margin_percent}% for all items in group'
        })
        
    except Exception as e:
        logger.error(f"Error applying bulk margin: {str(e)}")
        return jsonify({'error': str(e)}), 500


@quote_pricing_bp.route('/api/quotes/<quote_id>/groups/<group_id>/bulk-discount', methods=['PUT'])
@cross_origin()
def apply_bulk_discount(quote_id, group_id):
    """
    Apply bulk discount adjustment to all items in a group
    """
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({'error': 'No request data provided'}), 400
        
        quote_data = request_data.get('quote', {})
        discount_percent = request_data.get('discountPercent')
        
        if discount_percent is None:
            return jsonify({'error': 'Discount percentage is required'}), 400
        
        # Apply bulk discount adjustment
        adjusted_quote = pricing_service.apply_bulk_discount_adjustment(
            quote_data, group_id, discount_percent
        )
        
        logger.info(f"Applied bulk discount {discount_percent}% to group {group_id} in quote {quote_id}")
        
        return jsonify({
            'success': True,
            'quote': adjusted_quote,
            'message': f'Discount adjusted to {discount_percent}% for all items in group'
        })
        
    except Exception as e:
        logger.error(f"Error applying bulk discount: {str(e)}")
        return jsonify({'error': str(e)}), 500


@quote_pricing_bp.route('/api/quotes/<quote_id>/waste-calculation', methods=['POST'])
@cross_origin()
def calculate_waste_factor(quote_id):
    """
    Calculate quantity including waste factor
    """
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({'error': 'No request data provided'}), 400
        
        base_quantity = request_data.get('baseQuantity')
        waste_percent = request_data.get('wastePercent', 0)
        
        if base_quantity is None:
            return jsonify({'error': 'Base quantity is required'}), 400
        
        # Calculate quantity with waste
        final_quantity = pricing_service.calculate_waste_factor(base_quantity, waste_percent)
        
        return jsonify({
            'success': True,
            'baseQuantity': base_quantity,
            'wastePercent': waste_percent,
            'finalQuantity': final_quantity,
            'wasteAmount': final_quantity - base_quantity
        })
        
    except Exception as e:
        logger.error(f"Error calculating waste factor: {str(e)}")
        return jsonify({'error': str(e)}), 500


@quote_pricing_bp.route('/api/quotes/<quote_id>/stock-length-calculation', methods=['POST'])
@cross_origin()
def calculate_stock_length(quote_id):
    """
    Calculate optimal stock length and quantity for required length
    """
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({'error': 'No request data provided'}), 400
        
        required_length = request_data.get('requiredLength')
        stock_lengths = request_data.get('stockLengths', [])
        
        if required_length is None:
            return jsonify({'error': 'Required length is required'}), 400
        
        if not stock_lengths:
            return jsonify({'error': 'Stock lengths list is required'}), 400
        
        # Calculate optimal stock length and quantity
        selected_length, quantity_needed = pricing_service.round_up_to_stock_length(
            required_length, stock_lengths
        )
        
        total_supplied = selected_length * quantity_needed
        waste_amount = total_supplied - required_length
        waste_percent = (waste_amount / total_supplied) * 100 if total_supplied > 0 else 0
        
        return jsonify({
            'success': True,
            'requiredLength': required_length,
            'selectedStockLength': selected_length,
            'quantityNeeded': quantity_needed,
            'totalSupplied': total_supplied,
            'wasteAmount': waste_amount,
            'wastePercent': round(waste_percent, 2)
        })
        
    except Exception as e:
        logger.error(f"Error calculating stock length: {str(e)}")
        return jsonify({'error': str(e)}), 500


@quote_pricing_bp.route('/api/quotes/<quote_id>/composite-pricing', methods=['POST'])
@cross_origin()
def calculate_composite_pricing(quote_id):
    """
    Calculate pricing for composite items (tender rates)
    """
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({'error': 'No request data provided'}), 400
        
        composite_recipe = request_data.get('recipe', {})
        
        if not composite_recipe:
            return jsonify({'error': 'Composite recipe is required'}), 400
        
        # Calculate composite pricing
        pricing_result = pricing_service.calculate_composite_item_pricing(composite_recipe)
        
        return jsonify({
            'success': True,
            'pricing': pricing_result
        })
        
    except Exception as e:
        logger.error(f"Error calculating composite pricing: {str(e)}")
        return jsonify({'error': str(e)}), 500


@quote_pricing_bp.route('/api/quotes/<quote_id>/pricing-summary', methods=['GET'])
@cross_origin()
def get_pricing_summary(quote_id):
    """
    Get pricing summary and analysis for a quote
    """
    try:
        # This would typically fetch from database
        # For now, return a sample summary structure
        
        summary = {
            'quoteId': quote_id,
            'totalItems': 0,
            'totalGroups': 0,
            'costBreakdown': {
                'materials': 0,
                'labour': 0,
                'transport': 0,
                'overhead': 0
            },
            'marginAnalysis': {
                'averageMargin': 0,
                'lowestMargin': 0,
                'highestMargin': 0,
                'marginByGroup': []
            },
            'profitabilityMetrics': {
                'grossProfit': 0,
                'grossProfitPercent': 0,
                'netProfit': 0,
                'netProfitPercent': 0
            }
        }
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting pricing summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

