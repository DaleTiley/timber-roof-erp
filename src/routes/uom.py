from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.stock import UnitOfMeasure
from datetime import datetime

uom_bp = Blueprint('uom', __name__)

@uom_bp.route('/uom', methods=['GET'])
def get_units_of_measure():
    """Get all units of measure with optional filtering"""
    try:
        # Get query parameters
        search = request.args.get('search', '')
        unit_type = request.args.get('unit_type', '')
        is_active = request.args.get('is_active', '')
        is_base_unit = request.args.get('is_base_unit', '')
        
        # Build query
        query = UnitOfMeasure.query
        
        # Apply filters
        if search:
            query = query.filter(
                db.or_(
                    UnitOfMeasure.code.ilike(f'%{search}%'),
                    UnitOfMeasure.name.ilike(f'%{search}%'),
                    UnitOfMeasure.description.ilike(f'%{search}%')
                )
            )
        
        if unit_type:
            query = query.filter(UnitOfMeasure.unit_type == unit_type)
            
        if is_active:
            active_filter = is_active.lower() == 'true'
            query = query.filter(UnitOfMeasure.is_active == active_filter)
            
        if is_base_unit:
            base_filter = is_base_unit.lower() == 'true'
            query = query.filter(UnitOfMeasure.is_base_unit == base_filter)
        
        # Execute query
        units = query.order_by(UnitOfMeasure.unit_type, UnitOfMeasure.name).all()
        
        return jsonify({
            'success': True,
            'units': [unit.to_dict() for unit in units],
            'count': len(units)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@uom_bp.route('/uom/<int:uom_id>', methods=['GET'])
def get_unit_of_measure(uom_id):
    """Get a specific unit of measure by ID"""
    try:
        unit = UnitOfMeasure.query.get_or_404(uom_id)
        return jsonify({
            'success': True,
            'unit': unit.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@uom_bp.route('/uom', methods=['POST'])
def create_unit_of_measure():
    """Create a new unit of measure"""
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
        
        # Check if unit code already exists
        existing_unit = UnitOfMeasure.query.filter_by(code=data['code']).first()
        if existing_unit:
            return jsonify({
                'success': False,
                'error': 'Unit code already exists'
            }), 400
        
        # Validate base unit if provided
        base_unit_id = data.get('base_unit_id')
        if base_unit_id:
            base_unit = UnitOfMeasure.query.get(base_unit_id)
            if not base_unit:
                return jsonify({
                    'success': False,
                    'error': 'Base unit not found'
                }), 400
        
        # Create new unit of measure
        unit = UnitOfMeasure(
            code=data['code'],
            name=data['name'],
            description=data.get('description'),
            unit_type=data.get('unit_type'),
            base_unit_id=base_unit_id,
            conversion_factor=data.get('conversion_factor', 1.0),
            is_base_unit=data.get('is_base_unit', False),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(unit)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Unit of measure created successfully',
            'unit': unit.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@uom_bp.route('/uom/<int:uom_id>', methods=['PUT'])
def update_unit_of_measure(uom_id):
    """Update an existing unit of measure"""
    try:
        unit = UnitOfMeasure.query.get_or_404(uom_id)
        data = request.get_json()
        
        # Check if code is being changed and if it already exists
        if data.get('code') and data['code'] != unit.code:
            existing_unit = UnitOfMeasure.query.filter_by(code=data['code']).first()
            if existing_unit:
                return jsonify({
                    'success': False,
                    'error': 'Unit code already exists'
                }), 400
        
        # Validate base unit if being updated
        base_unit_id = data.get('base_unit_id')
        if base_unit_id and base_unit_id != unit.base_unit_id:
            base_unit = UnitOfMeasure.query.get(base_unit_id)
            if not base_unit:
                return jsonify({
                    'success': False,
                    'error': 'Base unit not found'
                }), 400
        
        # Update unit fields
        updateable_fields = [
            'code', 'name', 'description', 'unit_type', 'base_unit_id',
            'conversion_factor', 'is_base_unit', 'is_active'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(unit, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Unit of measure updated successfully',
            'unit': unit.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@uom_bp.route('/uom/<int:uom_id>', methods=['DELETE'])
def delete_unit_of_measure(uom_id):
    """Delete a unit of measure"""
    try:
        unit = UnitOfMeasure.query.get_or_404(uom_id)
        
        # Check if unit has associated stock items
        if unit.stock_items_stocked or unit.stock_items_sales or unit.stock_items_purchase:
            return jsonify({
                'success': False,
                'error': 'Cannot delete unit of measure with associated stock items'
            }), 400
        
        # Check if unit is used as base unit for other units
        if unit.derived_units:
            return jsonify({
                'success': False,
                'error': 'Cannot delete unit of measure that is used as base unit for other units'
            }), 400
        
        db.session.delete(unit)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Unit of measure deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@uom_bp.route('/uom/types', methods=['GET'])
def get_unit_types():
    """Get all unique unit types"""
    try:
        types = db.session.query(UnitOfMeasure.unit_type).distinct().filter(
            UnitOfMeasure.unit_type.isnot(None)
        ).all()
        
        type_list = [type_[0] for type_ in types if type_[0]]
        
        return jsonify({
            'success': True,
            'types': sorted(type_list)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@uom_bp.route('/uom/base-units', methods=['GET'])
def get_base_units():
    """Get all base units for dropdown selection"""
    try:
        base_units = UnitOfMeasure.query.filter_by(is_base_unit=True, is_active=True).order_by(UnitOfMeasure.name).all()
        
        return jsonify({
            'success': True,
            'base_units': [{'id': unit.id, 'code': unit.code, 'name': unit.name, 'unit_type': unit.unit_type} for unit in base_units]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

