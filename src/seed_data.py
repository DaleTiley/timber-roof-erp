import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.main import app
from src.models.user import db
from src.models.customer import Customer
from src.models.contact import Contact

def seed_data():
    """Seed the database with sample customers and contacts"""
    with app.app_context():
        # Clear existing data
        Contact.query.delete()
        Customer.query.delete()
        
        # Create sample customers
        customers_data = [
            {
                'name': 'ABC Construction Ltd',
                'company_type': 'Commercial Builder',
                'email': 'info@abcconstruction.com',
                'phone': '+27 11 123 4567',
                'address_line1': '123 Industrial Road',
                'city': 'Johannesburg',
                'province': 'Gauteng',
                'postal_code': '2001',
                'vat_number': '4123456789',
                'credit_limit': 50000.00,
                'payment_terms': 30,
                'status': 'Active'
            },
            {
                'name': 'XYZ Roofing Solutions',
                'company_type': 'Roofing Contractor',
                'email': 'contact@xyzroofing.co.za',
                'phone': '+27 21 987 6543',
                'address_line1': '456 Roof Street',
                'city': 'Cape Town',
                'province': 'Western Cape',
                'postal_code': '8001',
                'vat_number': '4987654321',
                'credit_limit': 75000.00,
                'payment_terms': 45,
                'status': 'Active'
            },
            {
                'name': 'Timber Masters CC',
                'company_type': 'Timber Supplier',
                'email': 'sales@timbermasters.co.za',
                'phone': '+27 31 555 0123',
                'address_line1': '789 Wood Avenue',
                'city': 'Durban',
                'province': 'KwaZulu-Natal',
                'postal_code': '4001',
                'vat_number': '4555012345',
                'credit_limit': 25000.00,
                'payment_terms': 30,
                'status': 'Active'
            },
            {
                'name': 'Elite Building Services',
                'company_type': 'General Contractor',
                'email': 'admin@elitebuilding.co.za',
                'phone': '+27 12 444 7890',
                'address_line1': '321 Builder Lane',
                'city': 'Pretoria',
                'province': 'Gauteng',
                'postal_code': '0001',
                'vat_number': '4444789012',
                'credit_limit': 100000.00,
                'payment_terms': 60,
                'status': 'Active'
            },
            {
                'name': 'Coastal Developments',
                'company_type': 'Property Developer',
                'email': 'projects@coastaldev.co.za',
                'phone': '+27 41 333 2468',
                'address_line1': '654 Ocean Drive',
                'city': 'Port Elizabeth',
                'province': 'Eastern Cape',
                'postal_code': '6001',
                'vat_number': '4333246810',
                'credit_limit': 150000.00,
                'payment_terms': 30,
                'status': 'Active'
            }
        ]
        
        customers = []
        for customer_data in customers_data:
            customer = Customer(**customer_data)
            db.session.add(customer)
            customers.append(customer)
        
        db.session.flush()  # Flush to get customer IDs
        
        # Create sample contacts
        contacts_data = [
            # ABC Construction Ltd contacts
            {
                'customer_id': customers[0].id,
                'first_name': 'John',
                'last_name': 'Smith',
                'title': 'Project Manager',
                'email': 'john.smith@abcconstruction.com',
                'phone': '+27 11 123 4567',
                'mobile': '+27 82 123 4567',
                'department': 'Projects',
                'is_primary': True,
                'is_technical': True,
                'status': 'Active'
            },
            {
                'customer_id': customers[0].id,
                'first_name': 'Mary',
                'last_name': 'Johnson',
                'title': 'Financial Manager',
                'email': 'mary.johnson@abcconstruction.com',
                'phone': '+27 11 123 4568',
                'mobile': '+27 82 123 4568',
                'department': 'Finance',
                'is_billing': True,
                'status': 'Active'
            },
            # XYZ Roofing Solutions contacts
            {
                'customer_id': customers[1].id,
                'first_name': 'Sarah',
                'last_name': 'Williams',
                'title': 'Operations Director',
                'email': 'sarah.williams@xyzroofing.co.za',
                'phone': '+27 21 987 6543',
                'mobile': '+27 83 987 6543',
                'department': 'Operations',
                'is_primary': True,
                'is_technical': True,
                'status': 'Active'
            },
            {
                'customer_id': customers[1].id,
                'first_name': 'David',
                'last_name': 'Brown',
                'title': 'Site Supervisor',
                'email': 'david.brown@xyzroofing.co.za',
                'phone': '+27 21 987 6544',
                'mobile': '+27 83 987 6544',
                'department': 'Operations',
                'is_technical': True,
                'status': 'Active'
            },
            # Timber Masters CC contacts
            {
                'customer_id': customers[2].id,
                'first_name': 'Michael',
                'last_name': 'Davis',
                'title': 'Sales Manager',
                'email': 'michael.davis@timbermasters.co.za',
                'phone': '+27 31 555 0123',
                'mobile': '+27 84 555 0123',
                'department': 'Sales',
                'is_primary': True,
                'status': 'Active'
            },
            # Elite Building Services contacts
            {
                'customer_id': customers[3].id,
                'first_name': 'Lisa',
                'last_name': 'Wilson',
                'title': 'Managing Director',
                'email': 'lisa.wilson@elitebuilding.co.za',
                'phone': '+27 12 444 7890',
                'mobile': '+27 85 444 7890',
                'department': 'Management',
                'is_primary': True,
                'is_billing': True,
                'status': 'Active'
            },
            {
                'customer_id': customers[3].id,
                'first_name': 'Robert',
                'last_name': 'Taylor',
                'title': 'Technical Manager',
                'email': 'robert.taylor@elitebuilding.co.za',
                'phone': '+27 12 444 7891',
                'mobile': '+27 85 444 7891',
                'department': 'Technical',
                'is_technical': True,
                'status': 'Active'
            },
            # Coastal Developments contacts
            {
                'customer_id': customers[4].id,
                'first_name': 'Jennifer',
                'last_name': 'Anderson',
                'title': 'Development Manager',
                'email': 'jennifer.anderson@coastaldev.co.za',
                'phone': '+27 41 333 2468',
                'mobile': '+27 86 333 2468',
                'department': 'Development',
                'is_primary': True,
                'is_technical': True,
                'status': 'Active'
            }
        ]
        
        for contact_data in contacts_data:
            contact = Contact(**contact_data)
            db.session.add(contact)
        
        db.session.commit()
        print(f"Successfully seeded {len(customers)} customers and {len(contacts_data)} contacts")

if __name__ == '__main__':
    seed_data()

