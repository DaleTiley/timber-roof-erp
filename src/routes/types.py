from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.stock import StockType
from datetime import datetime

types_bp = Blueprint('types', __name__)

@types_bp.route('/types', methods=['GET'])
def get_types():
    """Get all stock types with optional filtering"""
    try:
        # Get query parameters
        search = request.args.get('search', '')
        is_active = request.args.get('is_active', '')
        
        # Build query
        query = StockType.query
        
        # Apply filters
        if search:
            query = query.filter(
                db.or_(
                    StockType.code.ilike(f'%{search}%'),
                    StockType.name.ilike(f'%{search}%'),
                    StockType.description.ilike(f'%{search}%')
                )
            )
            
        if is_active:
            active_filter = is_active.lower() == 'true'
            query = query.filter(StockType.is_active == active_filter)
        
        # Execute query
        types = query.order_by(StockType.name).all()
        
        return jsonify({
            'success': True,
            'types': [type_.to_dict() for type_ in types],
            'count': len(types)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@types_bp.route('/types/<int:type_id>', methods=['GET'])
def get_type(type_id):
    """Get a specific type by ID"""
    try:
        type_ = StockType.query.get_or_404(type_id)
        return jsonify({
            'success': True,
            'type': type_.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@types_bp.route('/types', methods=['POST'])
def create_type():
    """Create a new stock type"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['code', 'name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        # Check if type code already exists
        existing_type = StockType.query.filter_by(code=data['code']).first()
        if existing_type:
            return jsonify({
                'success': False,
                'error': 'Type code already exists'
            }), 400
        
        # Create new type
        type_ = StockType(
            code=data['code'],
            name=data['name'],
            description=data.get('description'),
            properties=data.get('properties', {}),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(type_)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Type created successfully',
            'type': type_.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@types_bp.route('/types/<int:type_id>', methods=['PUT'])
def update_type(type_id):
    """Update an existing type"""
    try:
        type_ = StockType.query.get_or_404(type_id)
        data = request.get_json()
        
        # Check if code is being changed and if it already exists
        if data.get('code') and data['code'] != type_.code:
            existing_type = StockType.query.filter_by(code=data['code']).first()
            if existing_type:
                return jsonify({
                    'success': False,
                    'error': 'Type code already exists'
                }), 400
        
        # Update type fields
        updateable_fields = ['code', 'name', 'description', 'properties', 'is_active']
        
        for field in updateable_fields:
            if field in data:
                setattr(type_, field, data[field])
        
        type_.updated_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Type updated successfully',
            'type': type_.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@types_bp.route('/types/<int:type_id>', methods=['DELETE'])
def delete_type(type_id):
    """Delete a type"""
    try:
        type_ = StockType.query.get_or_404(type_id)
        
        # Check if type has associated stock items
        if type_.stock_items:
            return jsonify({
                'success': False,
                'error': 'Cannot delete type with associated stock items'
            }), 400
        
        db.session.delete(type_)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Type deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

