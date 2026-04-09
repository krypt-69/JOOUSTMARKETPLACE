from flask import Blueprint

# Create the main admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Import routes at the bottom to avoid circular imports
from app.admin import routes
