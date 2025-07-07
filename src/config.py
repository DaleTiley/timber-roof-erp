"""
Configuration module for ERP system
Handles database connections and environment settings

Added: 2025-01-07 - Database configuration for Azure SQL support
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        # Default to SQLite for development
        basedir = os.path.abspath(os.path.dirname(__file__))
        DATABASE_URL = f'sqlite:///{os.path.join(basedir, "database", "app.db")}'
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Application settings
    APP_NAME = os.environ.get('APP_NAME') or 'Timber Roof ERP'
    APP_VERSION = os.environ.get('APP_VERSION') or '1.0.0'
    
    # Flask settings
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries in development

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

class AzureSQLConfig(Config):
    """Azure SQL Database configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # Azure SQL specific settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'timeout': 30,
            'check_same_thread': False
        }
    }

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'azure': AzureSQLConfig,
    'default': DevelopmentConfig
}

