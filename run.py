"""
cGR8s - Comprehensive Goods Reconciliation at Secondary
Application entry point.
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

from app import create_app

app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5053))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
