from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.advanced_stock import StockCategory
from datetime import datetime

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all stock categories with optional filtering"""
    try:
        # Get query parameters
        search = request.args.get('search', '')
        category_type = request.args.get('category_type', '')
        is_active = request.args.get('is_active', '')
        
        # Build query
        query = StockCategory.query
        
        # Apply filters
        if search:
            query = query.filter(
                db.or_(
                    StockCategory.code.ilike(f'%{search}%'),
                    StockCategory.name.ilike(f'%{search}%'),
                    StockCategory.description.ilike(f'%{search}%')
                )
            )
        
        if category_type:
            query = query.filter(StockCategory.category_type == category_type)
            
        if is_active:
            active_filter = is_active.lower() == 'true'
            query = query.filter(StockCategory.is_active == active_filter)
        
        # Execute query
        categories = query.order_by(StockCategory.name).all()
        
        return jsonify({
            'success': True,
            'categories': [category.to_dict() for category in categories],
            'count': len(categories)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@categories_bp.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """Get a specific category by ID"""
    try:
        category = StockCategory.query.get_or_404(category_id)
        return jsonify({
            'success': True,
            'category': category.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@categories_bp.route('/categories', methods=['POST'])
def create_category():
    """Create a new stock category"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['code', 'name', 'category_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        # Check if category code already exists
        existing_category = StockCategory.query.filter_by(code=data['code']).first()
        if existing_category:
            return jsonify({
                'success': False,
                'error': 'Category code already exists'
            }), 400
        
        # Validate category type
        valid_types = ['STANDARD', 'MANUFACTURED', 'SERVICE', 'COMPOSITE']
        if data['category_type'] not in valid_types:
            return jsonify({
                'success': False,
                'error': f'Category type must be one of: {", ".join(valid_types)}'
            }), 400
        
        # Create new category
        category = StockCategory(
            code=data['code'],
            name=data['name'],
            description=data.get('description'),
            category_type=data['category_type'],
            is_active=data.get('is_active', True)
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Category created successfully',
            'category': category.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@categories_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Update an existing category"""
    try:
        category = StockCategory.query.get_or_404(category_id)
        data = request.get_json()
        
        # Check if code is being changed and if it already exists
        if data.get('code') and data['code'] != category.code:
            existing_category = StockCategory.query.filter_by(code=data['code']).first()
            if existing_category:
                return jsonify({
                    'success': False,
                    'error': 'Category code already exists'
                }), 400
        
        # Validate category type if being updated
        if data.get('category_type'):
            valid_types = ['STANDARD', 'MANUFACTURED', 'SERVICE', 'COMPOSITE']
            if data['category_type'] not in valid_types:
                return jsonify({
                    'success': False,
                    'error': f'Category type must be one of: {", ".join(valid_types)}'
                }), 400
        
        # Update category fields
        updateable_fields = ['code', 'name', 'description', 'category_type', 'is_active']
        
        for field in updateable_fields:
            if field in data:
                setattr(category, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Category updated successfully',
            'category': category.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@categories_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete a category"""
    try:
        category = StockCategory.query.get_or_404(category_id)
        
        # Check if category has associated stock items
        if category.stock_items:
            return jsonify({
                'success': False,
                'error': 'Cannot delete category with associated stock items'
            }), 400
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Category deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@categories_bp.route('/categories/types', methods=['GET'])
def get_category_types():
    """Get all available category types"""
    try:
        category_types = [
            {'code': 'STANDARD', 'name': 'Standard Items', 'description': 'Regular stock items with fixed properties'},
            {'code': 'MANUFACTURED', 'name': 'Manufactured Items', 'description': 'Items that are manufactured to order with BOMs'},
            {'code': 'SERVICE', 'name': 'Service Items', 'description': 'Service-based items like labor and transport'},
            {'code': 'COMPOSITE', 'name': 'Composite Items', 'description': 'Items made up of multiple components for tender rates'}
        ]
        
        return jsonify({
            'success': True,
            'category_types': category_types
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

