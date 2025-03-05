from flask import jsonify
from flask import Blueprint
from backend.providers.extensions import get_extensions_json

extensions_bp = Blueprint("extensions", __name__)

@extensions_bp.route('/', methods=['GET'])
def get_extensions():
    """API endpoint to fetch file extensions."""
    data = get_extensions_json()
    return jsonify(data), (200 if "error" not in data else 500)

