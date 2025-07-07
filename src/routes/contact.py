from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.contact import Contact
from src.models.customer import Customer
from sqlalchemy import or_
from datetime import datetime

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/contacts', methods=['GET'])
def get_contacts():
    """Get all contacts with optional search and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '', type=str)
        customer_id = request.args.get('customer_id', type=int)
        status = request.args.get('status', '', type=str)
        
        query = Contact.query.join(Customer)
        
        # Apply customer filter
        if customer_id:
            query = query.filter(Contact.customer_id == customer_id)
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    Contact.first_name.ilike(f'%{search}%'),
                    Contact.last_name.ilike(f'%{search}%'),
                    Contact.email.ilike(f'%{search}%'),
                    Customer.name.ilike(f'%{search}%')
                )
            )
        
        # Apply status filter
        if status:
            query = query.filter(Contact.status == status)
        
        # Order by customer name, then contact name
        query = query.order_by(Customer.name, Contact.first_name, Contact.last_name)
        
        # Paginate
        contacts = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'contacts': [contact.to_dict() for contact in contacts.items],
            'total': contacts.total,
            'pages': contacts.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@contact_bp.route('/contacts/<int:contact_id>', methods=['GET'])
def get_contact(contact_id):
    """Get a specific contact by ID"""
    try:
        contact = Contact.query.get_or_404(contact_id)
        return jsonify(contact.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@contact_bp.route('/contacts', methods=['POST'])
def create_contact():
    """Create a new contact"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('customer_id'):
            return jsonify({'error': 'Customer ID is required'}), 400
        if not data.get('first_name'):
            return jsonify({'error': 'First name is required'}), 400
        if not data.get('last_name'):
            return jsonify({'error': 'Last name is required'}), 400
        
        # Verify customer exists
        customer = Customer.query.get(data.get('customer_id'))
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # If this is set as primary contact, unset other primary contacts for this customer
        if data.get('is_primary'):
            Contact.query.filter_by(customer_id=data.get('customer_id'), is_primary=True).update({'is_primary': False})
        
        contact = Contact(
            customer_id=data.get('customer_id'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            title=data.get('title'),
            email=data.get('email'),
            phone=data.get('phone'),
            mobile=data.get('mobile'),
            department=data.get('department'),
            is_primary=data.get('is_primary', False),
            is_billing=data.get('is_billing', False),
            is_technical=data.get('is_technical', False),
            notes=data.get('notes'),
            status=data.get('status', 'Active')
        )
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify(contact.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@contact_bp.route('/contacts/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    """Update an existing contact"""
    try:
        contact = Contact.query.get_or_404(contact_id)
        data = request.get_json()
        
        # If this is set as primary contact, unset other primary contacts for this customer
        if data.get('is_primary') and not contact.is_primary:
            Contact.query.filter_by(customer_id=contact.customer_id, is_primary=True).update({'is_primary': False})
        
        # Update fields
        contact.first_name = data.get('first_name', contact.first_name)
        contact.last_name = data.get('last_name', contact.last_name)
        contact.title = data.get('title', contact.title)
        contact.email = data.get('email', contact.email)
        contact.phone = data.get('phone', contact.phone)
        contact.mobile = data.get('mobile', contact.mobile)
        contact.department = data.get('department', contact.department)
        contact.is_primary = data.get('is_primary', contact.is_primary)
        contact.is_billing = data.get('is_billing', contact.is_billing)
        contact.is_technical = data.get('is_technical', contact.is_technical)
        contact.notes = data.get('notes', contact.notes)
        contact.status = data.get('status', contact.status)
        contact.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(contact.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@contact_bp.route('/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Delete a contact"""
    try:
        contact = Contact.query.get_or_404(contact_id)
        
        db.session.delete(contact)
        db.session.commit()
        
        return jsonify({'message': 'Contact deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@contact_bp.route('/contacts/search', methods=['GET'])
def search_contacts():
    """Search contacts by name or email"""
    try:
        query = request.args.get('q', '', type=str)
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify({'contacts': []})
        
        contacts = Contact.query.join(Customer).filter(
            or_(
                Contact.first_name.ilike(f'%{query}%'),
                Contact.last_name.ilike(f'%{query}%'),
                Contact.email.ilike(f'%{query}%'),
                Customer.name.ilike(f'%{query}%')
            )
        ).filter(Contact.status == 'Active').limit(limit).all()
        
        return jsonify({
            'contacts': [contact.to_dict() for contact in contacts]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Statistics endpoint
@contact_bp.route('/contacts/stats', methods=['GET'])
def get_contact_stats():
    """Get contact statistics for dashboard"""
    try:
        total_contacts = Contact.query.count()
        active_contacts = Contact.query.filter_by(status='Active').count()
        primary_contacts = Contact.query.filter_by(is_primary=True).count()
        
        return jsonify({
            'total_contacts': total_contacts,
            'active_contacts': active_contacts,
            'primary_contacts': primary_contacts
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

