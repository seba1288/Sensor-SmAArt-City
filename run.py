#!/usr/bin/env python
"""
Main entry point for the IoT Sensor Monitoring Platform.
Run with: python run.py
"""

import os
import sys
from app import create_app, db

if __name__ == '__main__':
    # Get environment
    env = os.environ.get('FLASK_ENV', 'development')
    
    # Create app
    from app.config import DevelopmentConfig, ProductionConfig
    config = ProductionConfig if env == 'production' else DevelopmentConfig
    app = create_app(config)
    
    # Run Flask development server
    debug = env != 'production'
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=debug,
        use_reloader=debug,
    )
