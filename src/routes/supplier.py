from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.supplier import Supplier
from datetime import datetime

supplier_bp = Blueprint('supplier', __name__)

@supplier_bp.route('/suppliers', methods=['GET'])
def get_suppliers():
    """Get all suppliers with optional filtering"""
    try:
        # Get query parameters
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        status = request.args.get('status', '')
        is_active = request.args.get('is_active', '')
        
        # Build query
        query = Supplier.query
        
        # Apply filters
        if search:
            query = query.filter(
                db.or_(
                    Supplier.code.ilike(f'%{search}%'),
                    Supplier.name.ilike(f'%{search}%'),
                    Supplier.contact_person.ilike(f'%{search}%'),
                    Supplier.email.ilike(f'%{search}%')
                )
            )
        
        if category:
            query = query.filter(Supplier.supplier_category == category)
            
        if status:
            query = query.filter(Supplier.status == status)
            
        if is_active:
            active_filter = is_active.lower() == 'true'
            query = query.filter(Supplier.is_active == active_filter)
        
        # Execute query
        suppliers = query.order_by(Supplier.name).all()
        
        return jsonify({
            'success': True,
            'suppliers': [supplier.to_dict() for supplier in suppliers],
            'count': len(suppliers)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@supplier_bp.route('/suppliers/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    """Get a specific supplier by ID"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        return jsonify({
            'success': True,
            'supplier': supplier.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@supplier_bp.route('/suppliers', methods=['POST'])
def create_supplier():
    """Create a new supplier"""
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
        
        # Check if supplier code already exists
        existing_supplier = Supplier.query.filter_by(code=data['code']).first()
        if existing_supplier:
            return jsonify({
                'success': False,
                'error': 'Supplier code already exists'
            }), 400
        
        # Create new supplier
        supplier = Supplier(
            code=data['code'],
            name=data['name'],
            description=data.get('description'),
            contact_person=data.get('contact_person'),
            email=data.get('email'),
            phone=data.get('phone'),
            mobile=data.get('mobile'),
            fax=data.get('fax'),
            website=data.get('website'),
            address_line1=data.get('address_line1'),
            address_line2=data.get('address_line2'),
            city=data.get('city'),
            province=data.get('province'),
            postal_code=data.get('postal_code'),
            country=data.get('country', 'South Africa'),
            registration_number=data.get('registration_number'),
            vat_number=data.get('vat_number'),
            tax_number=data.get('tax_number'),
            payment_terms_days=data.get('payment_terms_days', 30),
            credit_limit=data.get('credit_limit', 0.0),
            currency=data.get('currency', 'ZAR'),
            supplier_category=data.get('supplier_category'),
            supplier_type=data.get('supplier_type', 'VENDOR'),
            status=data.get('status', 'ACTIVE'),
            is_active=data.get('is_active', True),
            notes=data.get('notes'),
            delivery_instructions=data.get('delivery_instructions'),
            quality_rating=data.get('quality_rating')
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Supplier created successfully',
            'supplier': supplier.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@supplier_bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    """Update an existing supplier"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        data = request.get_json()
        
        # Check if code is being changed and if it already exists
        if data.get('code') and data['code'] != supplier.code:
            existing_supplier = Supplier.query.filter_by(code=data['code']).first()
            if existing_supplier:
                return jsonify({
                    'success': False,
                    'error': 'Supplier code already exists'
                }), 400
        
        # Update supplier fields
        updateable_fields = [
            'code', 'name', 'description', 'contact_person', 'email', 'phone', 'mobile',
            'fax', 'website', 'address_line1', 'address_line2', 'city', 'province',
            'postal_code', 'country', 'registration_number', 'vat_number', 'tax_number',
            'payment_terms_days', 'credit_limit', 'currency', 'supplier_category',
            'supplier_type', 'status', 'is_active', 'notes', 'delivery_instructions',
            'quality_rating'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(supplier, field, data[field])
        
        supplier.updated_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Supplier updated successfully',
            'supplier': supplier.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@supplier_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    """Delete a supplier"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        
        # Check if supplier has associated stock items
        if supplier.stock_items:
            return jsonify({
                'success': False,
                'error': 'Cannot delete supplier with associated stock items'
            }), 400
        
        db.session.delete(supplier)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Supplier deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@supplier_bp.route('/suppliers/categories', methods=['GET'])
def get_supplier_categories():
    """Get all unique supplier categories"""
    try:
        categories = db.session.query(Supplier.supplier_category).distinct().filter(
            Supplier.supplier_category.isnot(None)
        ).all()
        
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return jsonify({
            'success': True,
            'categories': sorted(category_list)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

