import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
from src.models.user import db
from src.models.stock import StockType, UnitOfMeasure, MarginGroup, DiscountGroup, CommissionGroup, StockItem

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def seed_stock_data():
    app = create_app()
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Clear existing data
        StockItem.query.delete()
        StockType.query.delete()
        UnitOfMeasure.query.delete()
        MarginGroup.query.delete()
        DiscountGroup.query.delete()
        CommissionGroup.query.delete()
        
        # Create Stock Types
        stock_types = [
            StockType(code='TIMBER', name='Timber', description='Timber products for roof construction', 
                     properties={'grade_required': True, 'treatment_required': True, 'dimensions_required': True}),
            StockType(code='SHEET', name='Sheeting', description='Roofing sheeting materials',
                     properties={'profile_required': True, 'color_required': True, 'coating_required': True}),
            StockType(code='TILE', name='Concrete Tiles', description='Concrete roof tiles',
                     properties={'profile_required': True, 'color_required': True, 'finish_required': True}),
            StockType(code='HARDWARE', name='Hardware', description='Fasteners, brackets, and hardware',
                     properties={'material_required': True, 'coating_required': True}),
            StockType(code='INSULATION', name='Insulation', description='Roof insulation materials',
                     properties={'r_value_required': True, 'thickness_required': True})
        ]
        
        for stock_type in stock_types:
            db.session.add(stock_type)
        
        # Create Units of Measure
        uoms = [
            # Base units
            UnitOfMeasure(code='EA', name='Each', description='Individual items', unit_type='count', is_base_unit=True),
            UnitOfMeasure(code='M', name='Metre', description='Linear metre', unit_type='length', is_base_unit=True),
            UnitOfMeasure(code='KG', name='Kilogram', description='Weight in kilograms', unit_type='weight', is_base_unit=True),
            UnitOfMeasure(code='M2', name='Square Metre', description='Area in square metres', unit_type='area', is_base_unit=True),
            UnitOfMeasure(code='M3', name='Cubic Metre', description='Volume in cubic metres', unit_type='volume', is_base_unit=True),
            
            # Derived units
            UnitOfMeasure(code='MM', name='Millimetre', description='Length in millimetres', unit_type='length', conversion_factor=0.001),
            UnitOfMeasure(code='CM', name='Centimetre', description='Length in centimetres', unit_type='length', conversion_factor=0.01),
            UnitOfMeasure(code='G', name='Gram', description='Weight in grams', unit_type='weight', conversion_factor=0.001),
            UnitOfMeasure(code='T', name='Tonne', description='Weight in tonnes', unit_type='weight', conversion_factor=1000),
            UnitOfMeasure(code='LM', name='Linear Metre', description='Linear metre for timber', unit_type='length', conversion_factor=1.0),
            
            # Timber specific
            UnitOfMeasure(code='BF', name='Board Foot', description='Board foot for timber volume', unit_type='volume', conversion_factor=0.002359737),
            UnitOfMeasure(code='LEN', name='Length', description='Timber length', unit_type='length', conversion_factor=1.0),
            
            # Sheeting specific (corrugated iron example: 1m width = 0.762m2 coverage)
            UnitOfMeasure(code='SHEET', name='Sheet', description='Individual sheet', unit_type='count', conversion_factor=1.0),
            UnitOfMeasure(code='M2COV', name='M2 Coverage', description='Square metre coverage', unit_type='area', conversion_factor=1.0)
        ]
        
        for uom in uoms:
            db.session.add(uom)
        
        # Set base unit relationships
        db.session.flush()  # Flush to get IDs
        
        # Update base unit references
        m_base = UnitOfMeasure.query.filter_by(code='M').first()
        kg_base = UnitOfMeasure.query.filter_by(code='KG').first()
        
        for uom in UnitOfMeasure.query.filter(UnitOfMeasure.unit_type.in_(['length'])).all():
            if not uom.is_base_unit:
                uom.base_unit_id = m_base.id
                
        for uom in UnitOfMeasure.query.filter(UnitOfMeasure.unit_type.in_(['weight'])).all():
            if not uom.is_base_unit:
                uom.base_unit_id = kg_base.id
        
        # Create Margin Groups
        margin_groups = [
            MarginGroup(code='STANDARD', name='Standard Margin', description='Standard margin for most items', default_margin_percentage=25.0),
            MarginGroup(code='PREMIUM', name='Premium Margin', description='Higher margin for premium products', default_margin_percentage=35.0),
            MarginGroup(code='COMMODITY', name='Commodity Margin', description='Lower margin for commodity items', default_margin_percentage=15.0),
            MarginGroup(code='CUSTOM', name='Custom Margin', description='Custom margin for special items', default_margin_percentage=30.0)
        ]
        
        for margin_group in margin_groups:
            db.session.add(margin_group)
        
        # Create Discount Groups
        discount_groups = [
            DiscountGroup(code='NONE', name='No Discount', description='No standard discount', default_discount_percentage=0.0),
            DiscountGroup(code='TRADE', name='Trade Discount', description='Trade customer discount', default_discount_percentage=10.0),
            DiscountGroup(code='VOLUME', name='Volume Discount', description='High volume discount', default_discount_percentage=15.0),
            DiscountGroup(code='SPECIAL', name='Special Discount', description='Special pricing discount', default_discount_percentage=20.0)
        ]
        
        for discount_group in discount_groups:
            db.session.add(discount_group)
        
        # Create Commission Groups
        commission_groups = [
            CommissionGroup(code='STANDARD', name='Standard Commission', description='Standard sales commission', default_commission_percentage=5.0),
            CommissionGroup(code='HIGH', name='High Commission', description='Higher commission for difficult sales', default_commission_percentage=8.0),
            CommissionGroup(code='LOW', name='Low Commission', description='Lower commission for easy sales', default_commission_percentage=3.0),
            CommissionGroup(code='NONE', name='No Commission', description='No commission items', default_commission_percentage=0.0)
        ]
        
        for commission_group in commission_groups:
            db.session.add(commission_group)
        
        db.session.flush()  # Flush to get IDs for relationships
        
        # Get IDs for relationships
        timber_type = StockType.query.filter_by(code='TIMBER').first()
        sheet_type = StockType.query.filter_by(code='SHEET').first()
        tile_type = StockType.query.filter_by(code='TILE').first()
        hardware_type = StockType.query.filter_by(code='HARDWARE').first()
        
        ea_uom = UnitOfMeasure.query.filter_by(code='EA').first()
        m_uom = UnitOfMeasure.query.filter_by(code='M').first()
        m2_uom = UnitOfMeasure.query.filter_by(code='M2').first()
        lm_uom = UnitOfMeasure.query.filter_by(code='LM').first()
        sheet_uom = UnitOfMeasure.query.filter_by(code='SHEET').first()
        
        standard_margin = MarginGroup.query.filter_by(code='STANDARD').first()
        premium_margin = MarginGroup.query.filter_by(code='PREMIUM').first()
        
        none_discount = DiscountGroup.query.filter_by(code='NONE').first()
        trade_discount = DiscountGroup.query.filter_by(code='TRADE').first()
        
        standard_commission = CommissionGroup.query.filter_by(code='STANDARD').first()
        high_commission = CommissionGroup.query.filter_by(code='HIGH').first()
        
        # Create Sample Stock Items
        stock_items = [
            # Timber items
            StockItem(
                code='TIM-90x35-H2',
                description='90x35 H2 Treated Pine',
                long_description='90mm x 35mm H2 treated pine timber for general construction',
                stock_type_id=timber_type.id,
                stocked_uom_id=lm_uom.id,
                sales_uom_id=lm_uom.id,
                purchase_uom_id=lm_uom.id,
                sales_to_stock_factor=1.0,
                purchase_to_stock_factor=1.0,
                standard_cost=8.50,
                last_cost=8.50,
                average_cost=8.50,
                margin_group_id=standard_margin.id,
                discount_group_id=trade_discount.id,
                commission_group_id=standard_commission.id,
                properties={
                    'width': 90,
                    'height': 35,
                    'grade': 'MGP10',
                    'treatment': 'H2',
                    'species': 'Pine'
                },
                minimum_stock_level=100.0,
                reorder_level=200.0,
                reorder_quantity=500.0,
                created_by='system'
            ),
            StockItem(
                code='TIM-140x45-H2',
                description='140x45 H2 Treated Pine',
                long_description='140mm x 45mm H2 treated pine timber for structural use',
                stock_type_id=timber_type.id,
                stocked_uom_id=lm_uom.id,
                sales_uom_id=lm_uom.id,
                purchase_uom_id=lm_uom.id,
                sales_to_stock_factor=1.0,
                purchase_to_stock_factor=1.0,
                standard_cost=15.75,
                last_cost=15.75,
                average_cost=15.75,
                margin_group_id=standard_margin.id,
                discount_group_id=trade_discount.id,
                commission_group_id=standard_commission.id,
                properties={
                    'width': 140,
                    'height': 45,
                    'grade': 'F7',
                    'treatment': 'H2',
                    'species': 'Pine'
                },
                minimum_stock_level=50.0,
                reorder_level=100.0,
                reorder_quantity=200.0,
                created_by='system'
            ),
            
            # Sheeting items
            StockItem(
                code='SHEET-CORR-762-COL',
                description='Corrugated Iron 0.42mm Colorbond',
                long_description='Corrugated iron sheeting 0.42mm Colorbond steel',
                stock_type_id=sheet_type.id,
                stocked_uom_id=sheet_uom.id if sheet_uom else ea_uom.id,
                sales_uom_id=m2_uom.id,
                purchase_uom_id=sheet_uom.id if sheet_uom else ea_uom.id,
                sales_to_stock_factor=0.762,  # 1 sheet = 0.762m2 coverage
                purchase_to_stock_factor=1.0,
                standard_cost=45.00,
                last_cost=45.00,
                average_cost=45.00,
                margin_group_id=premium_margin.id,
                discount_group_id=trade_discount.id,
                commission_group_id=high_commission.id,
                properties={
                    'profile': 'Corrugated',
                    'thickness': 0.42,
                    'coating': 'Colorbond',
                    'width': 762,
                    'coverage_width': 762
                },
                minimum_stock_level=20.0,
                reorder_level=50.0,
                reorder_quantity=100.0,
                created_by='system'
            ),
            
            # Hardware items
            StockItem(
                code='SCREW-ROOF-65MM',
                description='Roofing Screw 65mm',
                long_description='Self-drilling roofing screw 65mm with washer',
                stock_type_id=hardware_type.id,
                stocked_uom_id=ea_uom.id,
                sales_uom_id=ea_uom.id,
                purchase_uom_id=ea_uom.id,
                sales_to_stock_factor=1.0,
                purchase_to_stock_factor=1.0,
                standard_cost=0.25,
                last_cost=0.25,
                average_cost=0.25,
                margin_group_id=standard_margin.id,
                discount_group_id=none_discount.id,
                commission_group_id=standard_commission.id,
                properties={
                    'length': 65,
                    'material': 'Steel',
                    'coating': 'Zinc Plated',
                    'head_type': 'Hex',
                    'includes_washer': True
                },
                minimum_stock_level=1000.0,
                reorder_level=2000.0,
                reorder_quantity=5000.0,
                created_by='system'
            ),
            
            # Tile items
            StockItem(
                code='TILE-CONCRETE-TERRACOTTA',
                description='Concrete Tile Terracotta',
                long_description='Concrete roof tile in terracotta color',
                stock_type_id=tile_type.id,
                stocked_uom_id=ea_uom.id,
                sales_uom_id=m2_uom.id,
                purchase_uom_id=ea_uom.id,
                sales_to_stock_factor=10.5,  # 10.5 tiles per m2
                purchase_to_stock_factor=1.0,
                standard_cost=2.50,
                last_cost=2.50,
                average_cost=2.50,
                margin_group_id=premium_margin.id,
                discount_group_id=trade_discount.id,
                commission_group_id=high_commission.id,
                properties={
                    'profile': 'Mediterranean',
                    'color': 'Terracotta',
                    'finish': 'Glazed',
                    'coverage_per_tile': 0.095
                },
                minimum_stock_level=500.0,
                reorder_level=1000.0,
                reorder_quantity=2000.0,
                created_by='system'
            )
        ]
        
        for stock_item in stock_items:
            db.session.add(stock_item)
        
        db.session.commit()
        print("Stock data seeded successfully!")
        print(f"Created {len(stock_types)} stock types")
        print(f"Created {len(uoms)} units of measure")
        print(f"Created {len(margin_groups)} margin groups")
        print(f"Created {len(discount_groups)} discount groups")
        print(f"Created {len(commission_groups)} commission groups")
        print(f"Created {len(stock_items)} stock items")

if __name__ == '__main__':
    seed_stock_data()

