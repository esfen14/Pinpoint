"""Defines the /api blueprint and attaches the user, system and plugin sub-blueprints to it."""

from flask import Blueprint
from app.api import(
    user,
    system,
    plugin
)
# Registers the app-wide JSON handlers for 401 and 404.
from app.api import error_handlers

api_bp = Blueprint('api', __name__, url_prefix='/api')


# import modules
modules = [
    user.user_bp,
    system.system_bp,
    plugin.plugin_bp
    ]

for module in modules:
    api_bp.register_blueprint(module)