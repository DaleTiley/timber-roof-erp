# Timber Roof ERP System

A comprehensive ERP system designed specifically for timber roof design, manufacturing, delivery, and installation businesses.

## 🏗️ System Overview

This ERP system integrates with **Mitek Pamir** for roof design and provides complete business management from quotation to installation, including:

- **Project Management** - Complete project lifecycle management
- **Interactive Quote Grid** - Advanced quoting with GP distribution
- **Stock Management** - Complex timber stock with UOM handling
- **Customer & Contact Management** - Full CRM functionality
- **Mitek Integration** - Import variables and generate quotes
- **Financial Management** - GL entries, bank reconciliation, purchases

## 🚀 Features

### ✅ Currently Implemented
- **Project Workflow**: Projects → View → Create Quote → Interactive Quote Grid
- **Interactive Quote Grid**: Collapsible groups, live editing, GP distribution
- **Navigation Structure**: Home, Customers, Contacts, Projects, Stock, Activities
- **Backend APIs**: Complete REST API for all modules
- **Authentication**: User login and session management
- **Professional UI**: Dynamics 365-inspired responsive design

### 🔄 In Development
- **Advanced Stock Management**: Variable attributes, composite items, formulas
- **Mitek Integration**: Variable import and formula-based quantity calculation
- **Customer/Contact Forms**: Full CRUD operations
- **Financial Module**: GL entries and reporting

## 🛠️ Technology Stack

### Backend
- **Python 3.11** with Flask
- **SQLAlchemy** ORM
- **SQLite** (development) / **Azure SQL** (production)
- **Flask-CORS** for API access
- **RESTful API** architecture

### Frontend
- **React 18** with Vite
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Responsive Design** (desktop & mobile)

## 📦 Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- npm or yarn

### Backend Setup
```bash
cd erp-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

### Frontend Setup
```bash
cd erp-frontend
npm install
npm run dev
```

## 🗄️ Database Configuration

### Development (SQLite)
Default configuration uses SQLite for local development.

### Production (Azure SQL)
Set environment variables:
```bash
export DATABASE_URL="mssql+pyodbc://username:password@server.database.windows.net/database?driver=ODBC+Driver+17+for+SQL+Server"
export FLASK_ENV="production"
```

## 🚀 Deployment

### Current Live Demo
- **URL**: https://8xhpiqceoekz.manus.space
- **Login**: admin / password

### Production Deployment
1. Build frontend: `npm run build`
2. Copy build files to backend static folder
3. Deploy backend with environment variables
4. Configure Azure SQL connection

## 📋 Development Workflow

### Version Control Protocol
- ✅ **NEVER REBUILD** - Only modify what is specifically requested
- ✅ **INCREMENTAL ONLY** - Add/modify only requested functionality
- ✅ **PRESERVE EVERYTHING** - Assume everything else is exactly as wanted
- ✅ **TRACK CHANGES** - Every modification documented in CHANGELOG.md
- ✅ **ROLLBACK READY** - Can revert any specific change if needed

### Making Changes
1. Create feature branch
2. Make specific changes only
3. Update CHANGELOG.md
4. Test thoroughly
5. Create pull request
6. Deploy to production

## 📊 Business Logic

### Stock Management Complexity
- **Base Stock Items**: Standard inventory items
- **Variable Attribute Items**: Sheeting with colors, flashings with girths
- **Service Items**: Labour, transport, certification
- **Composite Items**: Tender rates with recipes (supplied & installed)
- **Temporary Items**: 120-day expiring codes for rare items
- **Formula Integration**: Automatic quantity calculation from Mitek variables

### Quote Workflow
1. **Project Creation** - Customer details and project info
2. **Quote Generation** - From project, create quote/tender/order
3. **Interactive Grid** - Add items, adjust quantities, apply formulas
4. **GP Distribution** - Set target GP and distribute across groups
5. **Approval Process** - Version control and approval workflow
6. **Order Creation** - Convert approved quote to production order

### Mitek Integration
- Import variables from Mitek Pamir exports
- Apply formulas to calculate quantities automatically
- Generate BOMs for manufactured items (timber trusses)
- Handle cut-to-length items with tallies

## 🔧 API Endpoints

### Core APIs
- `GET/POST /api/customers` - Customer management
- `GET/POST /api/contacts` - Contact management
- `GET/POST /api/projects` - Project management
- `GET/POST /api/stock` - Stock management
- `POST /api/quote-pricing/calculate` - Quote calculations
- `POST /api/quote-pricing/distribute-gp` - GP distribution

### Specialized APIs
- `/api/mitek/import` - Mitek variable import
- `/api/timber-uom/convert` - Timber UOM conversions
- `/api/formulas/test` - Formula testing and validation

## 📈 Roadmap

### Phase 1: Core Functionality ✅
- Project management
- Interactive quote grid
- Basic navigation

### Phase 2: Advanced Stock (In Progress)
- Variable attributes
- Composite items
- Formula system

### Phase 3: Mitek Integration
- Variable import
- Formula-based calculations
- BOM generation

### Phase 4: Financial Module
- GL entries
- Bank reconciliation
- Purchase management

### Phase 5: Production Control
- Order management
- Delivery tracking
- Installation management

## 🤝 Contributing

1. Follow the incremental development protocol
2. Document all changes in CHANGELOG.md
3. Test thoroughly before committing
4. Use descriptive commit messages
5. Create pull requests for review

## 📄 License

Proprietary - All rights reserved

## 📞 Support

For support and feature requests, please create an issue in this repository.

---

**Built for timber roof specialists who demand precision, efficiency, and complete business control.**

