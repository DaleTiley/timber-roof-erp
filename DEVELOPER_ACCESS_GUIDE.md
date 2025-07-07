# Developer Access Guide - Timber Roof ERP System

## 🎯 **Overview**
This guide explains how to give your developer proper access to the ERP system codebase and infrastructure.

---

## 🔧 **GitHub Repository Access**

### Method 1: Add as Collaborator (Recommended for Single Developer)

1. **Go to Repository Settings**
   - Navigate to your GitHub repository
   - Click **Settings** tab
   - Click **Collaborators** in left sidebar

2. **Add Developer**
   - Click **"Add people"** button
   - Enter developer's GitHub username or email
   - Select permission level:
     - **Write** ✅ (Recommended) - Can push code, create branches, review PRs
     - **Admin** - Full access (same as owner)
     - **Read** - View only (not suitable for development)

3. **Developer Accepts Invitation**
   - Developer receives email invitation
   - Must accept to gain access

### Method 2: GitHub Organization (Professional Setup)

1. **Create Organization**
   - GitHub → **Your profile** → **Your organizations** → **New organization**
   - Organization name: `mroofing` or `mroofing-systems`
   - Billing email: `dale@mroofing.co.za`

2. **Transfer Repository**
   - Repository → **Settings** → **Transfer ownership**
   - Transfer to your new organization

3. **Invite Developer to Organization**
   - Organization → **People** → **Invite member**
   - Set role: **Member** or **Owner**

---

## 🗄️ **Azure Portal Access**

### Grant Azure Subscription Access

1. **Azure Portal** → **Subscriptions**
2. Select your subscription
3. **Access control (IAM)** → **Add** → **Add role assignment**
4. **Role**: Select appropriate level:
   - **Contributor** ✅ (Recommended) - Can manage all resources except access
   - **Owner** - Full access including user management
   - **Reader** - View only access

5. **Assign access to**: User, group, or service principal
6. **Select**: Enter developer's email address
7. **Review + assign**

### Resource Group Access (Alternative)

1. **Resource Groups** → **TimberRoofERP-RG**
2. **Access control (IAM)** → **Add role assignment**
3. **Role**: **Contributor**
4. **Select**: Developer's email
5. **Save**

---

## 🗃️ **Database Access**

### Azure SQL Database User Creation

1. **Connect to Database** (using SQL Server Management Studio or Azure Query Editor)
2. **Run these commands** (replace `developer_email` with actual email):

```sql
-- Create login at server level
CREATE LOGIN [developer_email@domain.com] FROM EXTERNAL PROVIDER;

-- Switch to your database context
USE [TimberRoofERP];

-- Create user in database
CREATE USER [developer_email@domain.com] FROM EXTERNAL PROVIDER;

-- Grant permissions
ALTER ROLE db_datareader ADD MEMBER [developer_email@domain.com];
ALTER ROLE db_datawriter ADD MEMBER [developer_email@domain.com];
ALTER ROLE db_ddladmin ADD MEMBER [developer_email@domain.com];
```

### Alternative: SQL Authentication

```sql
-- Create SQL login
CREATE LOGIN developer_user WITH PASSWORD = 'SecurePassword123!';

-- Create database user
USE [TimberRoofERP];
CREATE USER developer_user FOR LOGIN developer_user;

-- Grant permissions
ALTER ROLE db_datareader ADD MEMBER developer_user;
ALTER ROLE db_datawriter ADD MEMBER developer_user;
ALTER ROLE db_ddladmin ADD MEMBER developer_user;
```

---

## 🚀 **App Service Deployment Access**

### Deployment Center Configuration

1. **App Service** → **Deployment Center**
2. **Source**: GitHub (already configured)
3. **Organization**: Your GitHub account
4. **Repository**: `timber-roof-erp`
5. **Branch**: `main`

### Developer Deployment Options

**Option A: Via GitHub** (Automatic)
- Developer pushes to `main` branch
- Azure automatically deploys changes

**Option B: Via Azure CLI**
- Developer needs Azure CLI installed
- Must be logged in with Azure account
- Can deploy directly: `az webapp up`

**Option C: Via Visual Studio Code**
- Install Azure App Service extension
- Connect to Azure account
- Deploy directly from VS Code

---

## 📋 **Information to Share with Developer**

### Repository Details
```
Repository URL: https://github.com/[your-username]/timber-roof-erp
Live Application: https://8xhpiqceoekz.manus.space
Documentation: README.md, DEPLOYMENT_GUIDE.md
```

### Database Connection (for Development)
```
Server: [your-server].database.windows.net
Database: TimberRoofERP
Authentication: Azure AD or SQL Authentication
Connection String: [provide full connection string]
```

### Environment Variables for Local Development
```
DATABASE_URL=mssql+pyodbc://[connection-string]
FLASK_ENV=development
SECRET_KEY=[your-secret-key]
APP_NAME=Timber Roof ERP
APP_VERSION=1.0.0
```

---

## 🔐 **Security Best Practices**

### What TO Share:
- ✅ GitHub repository access
- ✅ Azure resource access (Contributor level)
- ✅ Database development access
- ✅ App Service deployment access
- ✅ Documentation and guides
- ✅ Environment variables for development

### What NOT to Share:
- ❌ Your personal Azure admin credentials
- ❌ Production database admin passwords
- ❌ Domain management access
- ❌ Billing information access
- ❌ Subscription owner privileges

### Access Levels Summary:
| Resource | Recommended Access Level | Purpose |
|----------|-------------------------|---------|
| GitHub Repository | Write | Push code, create PRs |
| Azure Subscription | Contributor | Manage resources |
| SQL Database | db_datareader, db_datawriter, db_ddladmin | Full development access |
| App Service | Deployment access | Deploy applications |

---

## 👨‍💻 **Developer Onboarding Process**

### Step 1: Send Access Information
Email your developer with:
1. GitHub repository invitation
2. Azure portal access confirmation
3. Database connection details
4. This guide and all documentation

### Step 2: Developer Setup Checklist
Developer should complete:
- [ ] Accept GitHub repository invitation
- [ ] Clone repository locally
- [ ] Set up Python development environment
- [ ] Configure database connection
- [ ] Run application locally
- [ ] Test connection to Azure SQL
- [ ] Review existing code structure
- [ ] Read development workflow documentation

### Step 3: First Development Task
Suggested first task:
1. Make a small change (e.g., update a label)
2. Test locally
3. Create feature branch
4. Push to GitHub
5. Create Pull Request
6. Merge and verify deployment

---

## 🔄 **Collaboration Workflow**

### Development Process:
1. **Feature Development**
   ```bash
   git checkout -b feature/description
   # Make changes
   git add .
   git commit -m "ADD: Description of changes"
   git push origin feature/description
   ```

2. **Pull Request Process**
   - Create PR on GitHub
   - Review changes together
   - Test on development environment
   - Merge to main branch

3. **Deployment**
   - Automatic deployment to Azure
   - Test on live system
   - Monitor for issues

### Code Review Guidelines:
- All changes must be documented in CHANGELOG.md
- Follow incremental development protocol
- Test thoroughly before merging
- Use descriptive commit messages

---

## 📞 **Support and Communication**

### Regular Check-ins:
- Weekly progress reviews
- Code review sessions
- Planning for new features
- Issue resolution

### Communication Channels:
- GitHub Issues for bug reports
- Pull Request comments for code review
- Direct communication for urgent matters
- Documentation updates for process changes

---

## 🚨 **Emergency Access Removal**

### If Access Needs to be Revoked:

**GitHub:**
- Repository → Settings → Collaborators → Remove

**Azure:**
- Subscription → Access control (IAM) → Remove role assignment

**Database:**
```sql
DROP USER [developer_email@domain.com];
DROP LOGIN [developer_email@domain.com];
```

---

**This guide ensures secure, professional collaboration while maintaining control over your business-critical ERP system.**

