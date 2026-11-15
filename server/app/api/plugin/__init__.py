"""Defines the /plugin blueprint and loads the Plugin Manager routes."""

from flask import Blueprint

plugin_bp = Blueprint('plugin', __name__, url_prefix='/plugin')

from app.api.plugin import manager
