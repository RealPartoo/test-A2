from flask import Blueprint, render_template
vendor = Blueprint("vendor", __name__)

# If later you need vendor-only routes (upload, manage, etc.)
# you can put them here and register the blueprint in __init__.py.
# For now we keep it minimal to avoid duplicate endpoints.
