from flask import Blueprint

announcements_bp = Blueprint('announcements', __name__, url_prefix='/announcements')

from app.announcements import routes