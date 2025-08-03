#!/usr/bin/env python3
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the Flask app
from src.main import app

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Millennium Roofing ERP on port {port}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path}")
    
    app.run(host='0.0.0.0', port=port, debug=True)
