from flask import Blueprint, request, jsonify
from sqlalchemy import or_, and_
from src.models.stock import db, StockItem, StockType, UnitOfMeasure, MarginGroup, DiscountGroup, CommissionGroup
from datetime import datetime

stock_bp = Blueprint('stock', __name__)

# Stock Items Routes
@stock_bp.route('/stock-items', methods=['GET'])
def get_stock_items():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        stock_type_id = request.args.get('stock_type_id', type=int)
        is_active = request.args.get('is_active', type=bool)
        
        query = StockItem.query
        
        # Apply filters
        if search:
            query = query.filter(or_(
                StockItem.code.ilike(f'%{search}%'),
                StockItem.description.ilike(f'%{search}%')
            ))
        
        if stock_type_id:
            query = query.filter(StockItem.stock_type_id == stock_type_id)
            
        if is_active is not None:
            query = query.filter(StockItem.is_active == is_active)
        
        # Order by code
        query = query.order_by(StockItem.code)
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        stock_items = pagination.items
        
        return jsonify({
            'stock_items': [item.to_dict() for item in stock_items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/stock-items/<int:item_id>', methods=['GET'])
def get_stock_item(item_id):
    try:
        stock_item = StockItem.query.get_or_404(item_id)
        return jsonify(stock_item.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/stock-items', methods=['POST'])
def create_stock_item():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['code', 'description', 'stock_type_id', 'stocked_uom_id', 'sales_uom_id', 'purchase_uom_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if code already exists
        existing_item = StockItem.query.filter_by(code=data['code']).first()
        if existing_item:
            return jsonify({'error': 'Stock item code already exists'}), 400
        
        stock_item = StockItem(
            code=data['code'],
            description=data['description'],
            long_description=data.get('long_description'),
            stock_type_id=data['stock_type_id'],
            stocked_uom_id=data['stocked_uom_id'],
            sales_uom_id=data['sales_uom_id'],
            purchase_uom_id=data['purchase_uom_id'],
            sales_to_stock_factor=data.get('sales_to_stock_factor', 1.0),
            purchase_to_stock_factor=data.get('purchase_to_stock_factor', 1.0),
            standard_cost=data.get('standard_cost', 0.0),
            last_cost=data.get('last_cost', 0.0),
            average_cost=data.get('average_cost', 0.0),
            margin_group_id=data.get('margin_group_id'),
            discount_group_id=data.get('discount_group_id'),
            commission_group_id=data.get('commission_group_id'),
            properties=data.get('properties'),
            track_stock=data.get('track_stock', True),
            minimum_stock_level=data.get('minimum_stock_level', 0.0),
            maximum_stock_level=data.get('maximum_stock_level', 0.0),
            reorder_level=data.get('reorder_level', 0.0),
            reorder_quantity=data.get('reorder_quantity', 0.0),
            is_active=data.get('is_active', True),
            is_sellable=data.get('is_sellable', True),
            is_purchasable=data.get('is_purchasable', True),
            created_by=data.get('created_by', 'system')
        )
        
        db.session.add(stock_item)
        db.session.commit()
        
        return jsonify(stock_item.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/stock-items/<int:item_id>', methods=['PUT'])
def update_stock_item(item_id):
    try:
        stock_item = StockItem.query.get_or_404(item_id)
        data = request.get_json()
        
        # Check if code is being changed and if it already exists
        if 'code' in data and data['code'] != stock_item.code:
            existing_item = StockItem.query.filter_by(code=data['code']).first()
            if existing_item:
                return jsonify({'error': 'Stock item code already exists'}), 400
        
        # Update fields
        for field in ['code', 'description', 'long_description', 'stock_type_id', 
                     'stocked_uom_id', 'sales_uom_id', 'purchase_uom_id',
                     'sales_to_stock_factor', 'purchase_to_stock_factor',
                     'standard_cost', 'last_cost', 'average_cost',
                     'margin_group_id', 'discount_group_id', 'commission_group_id',
                     'properties', 'track_stock', 'minimum_stock_level',
                     'maximum_stock_level', 'reorder_level', 'reorder_quantity',
                     'is_active', 'is_sellable', 'is_purchasable']:
            if field in data:
                setattr(stock_item, field, data[field])
        
        stock_item.updated_date = datetime.utcnow()
        stock_item.updated_by = data.get('updated_by', 'system')
        
        db.session.commit()
        
        return jsonify(stock_item.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/stock-items/<int:item_id>', methods=['DELETE'])
def delete_stock_item(item_id):
    try:
        stock_item = StockItem.query.get_or_404(item_id)
        db.session.delete(stock_item)
        db.session.commit()
        
        return jsonify({'message': 'Stock item deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Stock Types Routes
@stock_bp.route('/stock-types', methods=['GET'])
def get_stock_types():
    try:
        stock_types = StockType.query.filter_by(is_active=True).order_by(StockType.name).all()
        return jsonify([stock_type.to_dict() for stock_type in stock_types])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/stock-types', methods=['POST'])
def create_stock_type():
    try:
        data = request.get_json()
        
        # Check if code already exists
        existing_type = StockType.query.filter_by(code=data['code']).first()
        if existing_type:
            return jsonify({'error': 'Stock type code already exists'}), 400
        
        stock_type = StockType(
            code=data['code'],
            name=data['name'],
            description=data.get('description'),
            properties=data.get('properties'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(stock_type)
        db.session.commit()
        
        return jsonify(stock_type.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Units of Measure Routes
@stock_bp.route('/units-of-measure', methods=['GET'])
def get_units_of_measure():
    try:
        uoms = UnitOfMeasure.query.filter_by(is_active=True).order_by(UnitOfMeasure.name).all()
        return jsonify([uom.to_dict() for uom in uoms])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/units-of-measure', methods=['POST'])
def create_unit_of_measure():
    try:
        data = request.get_json()
        
        # Check if code already exists
        existing_uom = UnitOfMeasure.query.filter_by(code=data['code']).first()
        if existing_uom:
            return jsonify({'error': 'UOM code already exists'}), 400
        
        uom = UnitOfMeasure(
            code=data['code'],
            name=data['name'],
            description=data.get('description'),
            unit_type=data.get('unit_type'),
            base_unit_id=data.get('base_unit_id'),
            conversion_factor=data.get('conversion_factor', 1.0),
            is_base_unit=data.get('is_base_unit', False),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(uom)
        db.session.commit()
        
        return jsonify(uom.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Margin Groups Routes
@stock_bp.route('/margin-groups', methods=['GET'])
def get_margin_groups():
    try:
        margin_groups = MarginGroup.query.filter_by(is_active=True).order_by(MarginGroup.name).all()
        return jsonify([group.to_dict() for group in margin_groups])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/margin-groups', methods=['POST'])
def create_margin_group():
    try:
        data = request.get_json()
        
        # Check if code already exists
        existing_group = MarginGroup.query.filter_by(code=data['code']).first()
        if existing_group:
            return jsonify({'error': 'Margin group code already exists'}), 400
        
        margin_group = MarginGroup(
            code=data['code'],
            name=data['name'],
            description=data.get('description'),
            default_margin_percentage=data.get('default_margin_percentage', 0.0),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(margin_group)
        db.session.commit()
        
        return jsonify(margin_group.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Discount Groups Routes
@stock_bp.route('/discount-groups', methods=['GET'])
def get_discount_groups():
    try:
        discount_groups = DiscountGroup.query.filter_by(is_active=True).order_by(DiscountGroup.name).all()
        return jsonify([group.to_dict() for group in discount_groups])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/discount-groups', methods=['POST'])
def create_discount_group():
    try:
        data = request.get_json()
        
        # Check if code already exists
        existing_group = DiscountGroup.query.filter_by(code=data['code']).first()
        if existing_group:
            return jsonify({'error': 'Discount group code already exists'}), 400
        
        discount_group = DiscountGroup(
            code=data['code'],
            name=data['name'],
            description=data.get('description'),
            default_discount_percentage=data.get('default_discount_percentage', 0.0),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(discount_group)
        db.session.commit()
        
        return jsonify(discount_group.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Commission Groups Routes
@stock_bp.route('/commission-groups', methods=['GET'])
def get_commission_groups():
    try:
        commission_groups = CommissionGroup.query.filter_by(is_active=True).order_by(CommissionGroup.name).all()
        return jsonify([group.to_dict() for group in commission_groups])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/commission-groups', methods=['POST'])
def create_commission_group():
    try:
        data = request.get_json()
        
        # Check if code already exists
        existing_group = CommissionGroup.query.filter_by(code=data['code']).first()
        if existing_group:
            return jsonify({'error': 'Commission group code already exists'}), 400
        
        commission_group = CommissionGroup(
            code=data['code'],
            name=data['name'],
            description=data.get('description'),
            default_commission_percentage=data.get('default_commission_percentage', 0.0),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(commission_group)
        db.session.commit()
        
        return jsonify(commission_group.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

