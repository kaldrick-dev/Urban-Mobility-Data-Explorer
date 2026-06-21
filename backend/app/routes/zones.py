from flask import Blueprint, jsonify
from app.services.zone_service import get_boroughs

zones_bp = Blueprint("zones", __name__)

@zones_bp.route("/zones/boroughs")
def boroughs():
    rows = get_boroughs()
    return jsonify({"data": [r["borough"] for r in rows]})
