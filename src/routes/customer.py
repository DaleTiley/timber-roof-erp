from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.customer import Customer
from src.models.contact import Contact
from sqlalchemy import or_
from datetime import datetime

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/customers', methods=['GET'])
def get_customers():
    """Get all customers with optional search and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '', type=str)
        status = request.args.get('status', '', type=str)
        
        query = Customer.query
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    Customer.name.ilike(f'%{search}%'),
                    Customer.email.ilike(f'%{search}%'),
                    Customer.company_type.ilike(f'%{search}%')
                )
            )
        
        # Apply status filter
        if status:
            query = query.filter(Customer.status == status)
        
        # Order by name
        query = query.order_by(Customer.name)
        
        # Paginate
        customers = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'customers': [customer.to_dict() for customer in customers.items],
            'total': customers.total,
            'pages': customers.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get a specific customer by ID"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        return jsonify(customer.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/customers', methods=['POST'])
def create_customer():
    """Create a new customer"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Customer name is required'}), 400
        
        customer = Customer(
            name=data.get('name'),
            company_type=data.get('company_type'),
            email=data.get('email'),
            phone=data.get('phone'),
            address_line1=data.get('address_line1'),
            address_line2=data.get('address_line2'),
            city=data.get('city'),
            province=data.get('province'),
            postal_code=data.get('postal_code'),
            country=data.get('country', 'South Africa'),
            vat_number=data.get('vat_number'),
            registration_number=data.get('registration_number'),
            credit_limit=data.get('credit_limit', 0.00),
            payment_terms=data.get('payment_terms', 30),
            discount_group_id=data.get('discount_group_id'),
            margin_group_id=data.get('margin_group_id'),
            status=data.get('status', 'Active'),
            notes=data.get('notes')
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return jsonify(customer.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Update an existing customer"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        data = request.get_json()
        
        # Update fields
        customer.name = data.get('name', customer.name)
        customer.company_type = data.get('company_type', customer.company_type)
        customer.email = data.get('email', customer.email)
        customer.phone = data.get('phone', customer.phone)
        customer.address_line1 = data.get('address_line1', customer.address_line1)
        customer.address_line2 = data.get('address_line2', customer.address_line2)
        customer.city = data.get('city', customer.city)
        customer.province = data.get('province', customer.province)
        customer.postal_code = data.get('postal_code', customer.postal_code)
        customer.country = data.get('country', customer.country)
        customer.vat_number = data.get('vat_number', customer.vat_number)
        customer.registration_number = data.get('registration_number', customer.registration_number)
        customer.credit_limit = data.get('credit_limit', customer.credit_limit)
        customer.payment_terms = data.get('payment_terms', customer.payment_terms)
        customer.discount_group_id = data.get('discount_group_id', customer.discount_group_id)
        customer.margin_group_id = data.get('margin_group_id', customer.margin_group_id)
        customer.status = data.get('status', customer.status)
        customer.notes = data.get('notes', customer.notes)
        customer.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(customer.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete a customer"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        # Check if customer has associated contacts or projects
        if customer.contacts:
            return jsonify({'error': 'Cannot delete customer with associated contacts. Delete contacts first.'}), 400
        
        db.session.delete(customer)
        db.session.commit()
        
        return jsonify({'message': 'Customer deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/customers/<int:customer_id>/contacts', methods=['GET'])
def get_customer_contacts(customer_id):
    """Get all contacts for a specific customer"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        contacts = Contact.query.filter_by(customer_id=customer_id).order_by(Contact.first_name).all()
        
        return jsonify({
            'customer': customer.to_dict(),
            'contacts': [contact.to_dict() for contact in contacts]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Statistics endpoint
@customer_bp.route('/customers/stats', methods=['GET'])
def get_customer_stats():
    """Get customer statistics for dashboard"""
    try:
        total_customers = Customer.query.count()
        active_customers = Customer.query.filter_by(status='Active').count()
        inactive_customers = Customer.query.filter_by(status='Inactive').count()
        
        # Recent customers (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_customers = Customer.query.filter(Customer.created_at >= thirty_days_ago).count()
        
        return jsonify({
            'total_customers': total_customers,
            'active_customers': active_customers,
            'inactive_customers': inactive_customers,
            'recent_customers': recent_customers
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

