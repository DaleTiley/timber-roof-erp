# Deployment Guide - Timber Roof ERP System

## 🎯 **Overview**
This guide will help you deploy the ERP system to production using:
- **GitHub** for code repository
- **Azure SQL Database** for data storage
- **Azure App Service** for hosting

---

## 📋 **Prerequisites**
- Microsoft 365 account: `dale@mroofing.co.za`
- Azure subscription (included with Microsoft 365)
- Domain: `mroofing.co.za`

---

## 🔧 **Step 1: GitHub Setup**

### Create GitHub Account
1. Go to **https://github.com**
2. Click **"Sign up"**
3. Email: `dale@mroofing.co.za`
4. Username: `dale-mroofing` (or your preference)
5. Password: Create secure password
6. Verify email from Microsoft 365

### Create Repository
1. Click **"New repository"** (green button)
2. Repository name: `timber-roof-erp`
3. Description: `Comprehensive ERP system for timber roof design, manufacturing, and installation`
4. Visibility: **Private** (recommended for business)
5. **Don't** initialize with README, .gitignore, or license (we have these)
6. Click **"Create repository"**

### Get Personal Access Token
1. GitHub → **Settings** (your profile) → **Developer settings**
2. **Personal access tokens** → **Tokens (classic)**
3. **Generate new token (classic)**
4. Name: `ERP Development`
5. Expiration: `90 days` (or your preference)
6. Scopes: Check **`repo`** (full repository access)
7. **Generate token** and **copy it immediately** (you won't see it again)

---

## 🗄️ **Step 2: Azure SQL Database**

### Create Database
1. **Azure Portal** → **SQL databases** → **Create**
2. **Subscription**: Your Microsoft 365 subscription
3. **Resource group**: Create new `TimberRoofERP-RG`
4. **Database name**: `TimberRoofERP`
5. **Server**: Create new
   - Server name: `mroofing-sql-server`
   - Location: `South Africa North` (or closest)
   - Authentication: **SQL authentication**
   - Admin login: `erpadmin`
   - Password: Create secure password
6. **Compute + storage**: Basic (5 DTU, 2GB) for development
7. **Backup storage redundancy**: Locally redundant
8. **Review + create**

### Configure Firewall
1. Go to your SQL server → **Networking**
2. **Add current client IP address**
3. **Allow Azure services** → Yes
4. **Save**

### Get Connection String
1. SQL Database → **Connection strings**
2. Copy the **ADO.NET** connection string
3. Replace `{your_password}` with your actual password

---

## 🚀 **Step 3: Deploy to Azure App Service**

### Create App Service
1. **Azure Portal** → **App Services** → **Create**
2. **Resource group**: `TimberRoofERP-RG`
3. **Name**: `mroofing-erp` (will be mroofing-erp.azurewebsites.net)
4. **Runtime stack**: `Python 3.11`
5. **Operating System**: Linux
6. **Region**: `South Africa North`
7. **Pricing plan**: Basic B1 (for development)
8. **Review + create**

### Configure Environment Variables
1. App Service → **Configuration** → **Application settings**
2. Add these settings:
   ```
   DATABASE_URL = [Your Azure SQL connection string]
   FLASK_ENV = production
   SECRET_KEY = [Generate random 32-character string]
   APP_NAME = Timber Roof ERP
   APP_VERSION = 1.0.0
   ```
3. **Save**

---

## 📤 **Step 4: Push Code to GitHub**

### Provide These Details to Manus:
- **GitHub Username**: `your-username`
- **Personal Access Token**: `ghp_xxxxxxxxxxxx`
- **Repository URL**: `https://github.com/your-username/timber-roof-erp`

### Manus Will Execute:
```bash
git remote add origin https://github.com/your-username/timber-roof-erp.git
git branch -M main
git push -u origin main
```

---

## 🔄 **Step 5: Continuous Deployment**

### Connect GitHub to Azure
1. App Service → **Deployment Center**
2. **Source**: GitHub
3. **Organization**: Your GitHub account
4. **Repository**: `timber-roof-erp`
5. **Branch**: `main`
6. **Build provider**: App Service build service
7. **Save**

### Deployment Pipeline
- Push to GitHub → Automatic deployment to Azure
- View logs in **Deployment Center** → **Logs**

---

## 🌐 **Step 6: Custom Domain (Optional)**

### Add Custom Domain
1. App Service → **Custom domains**
2. **Add custom domain**
3. Domain: `erp.mroofing.co.za`
4. **Validate**
5. Add DNS records to your domain provider:
   - **CNAME**: `erp` → `mroofing-erp.azurewebsites.net`
   - **TXT**: `asuid.erp` → `[verification code]`

### SSL Certificate
1. **Custom domains** → **Add binding**
2. **TLS/SSL type**: App Service Managed Certificate
3. **Binding type**: SNI SSL

---

## ✅ **Step 7: Testing**

### Health Check
- Visit: `https://mroofing-erp.azurewebsites.net/api/health`
- Should return: `{"status": "healthy", ...}`

### Application Access
- Visit: `https://mroofing-erp.azurewebsites.net`
- Login: `admin` / `password`
- Test all modules

---

## 🔧 **Development Workflow**

### Making Changes
1. **Local Development**:
   ```bash
   # Make changes to code
   git add .
   git commit -m "CHANGE: Description of what changed"
   git push origin main
   ```

2. **Automatic Deployment**: Azure will automatically deploy changes

3. **Testing**: Test on live site

4. **Rollback if needed**: 
   ```bash
   git revert [commit-hash]
   git push origin main
   ```

---

## 📞 **Support**

### What Manus Needs from You:
1. **GitHub username** after account creation
2. **Personal Access Token** for repository access
3. **Azure SQL connection string** after database creation
4. **Any custom domain preferences**

### What Manus Will Provide:
1. **Push code to GitHub**
2. **Configure deployment pipeline**
3. **Set up database migrations**
4. **Test deployment**
5. **Provide live URLs**

---

**Ready to start? Create your GitHub account and let me know your username and token!**

