from flask import Blueprint, jsonify, request
from app.services.zone_service import get_all_zones, get_zone_by_id, get_distinct_boroughs

zones_bp = Blueprint("zones", __name__)


@zones_bp.route("/zones", methods=["GET"])
def list_zones():
    borough = request.args.get("borough")
    zones = get_all_zones(borough)
    return jsonify({"success": True, "data": zones}), 200


@zones_bp.route("/zones/<int:zone_id>", methods=["GET"])
def get_zone(zone_id):
    zone = get_zone_by_id(zone_id)
    if not zone:
        return jsonify({"success": False, "message": "Zone not found."}), 404
    return jsonify({"success": True, "data": zone}), 200


@zones_bp.route("/zones/boroughs", methods=["GET"])
def list_boroughs():
    boroughs = get_distinct_boroughs()
    return jsonify({"success": True, "data": boroughs}), 200
