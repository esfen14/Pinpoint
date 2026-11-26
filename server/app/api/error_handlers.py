"""
JSON error envelope for the API errors that are raised before a route runs: a
signed-out request to a protected route (401) and an unknown /api path (404).
Without these handlers Flask answers with its default HTML error pages.
"""

from flask import request

from app import app, login
from app.api.helper.responses import error


@login.unauthorized_handler
def signed_out():
    """Return the 401 envelope when a signed-out request reaches a login_required route."""
    return error("You must be signed in to do that.", 401)


@app.errorhandler(404)
def not_found(exception):
    """Return the 404 envelope for paths under /api; other paths keep Flask's default page."""
    if request.path == "/api" or request.path.startswith("/api/"):
        return error("Not found.", 404)
    return exception
