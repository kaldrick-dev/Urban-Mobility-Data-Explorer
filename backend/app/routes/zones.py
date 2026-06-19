from flask import Blueprint, jsonify, request
from app.services.zone_service import get_all_zones, get_zone_by_id, get_zones_by_borough

zones_bp = Blueprint("zones", __name__)


@zones_bp.route("/zones", methods=["GET"])
def list_zones():
    """
    Returns all taxi zones.

    Query params:
      borough     filter by borough name (Manhattan, Brooklyn, Queens, Bronx, Staten Island, EWR)
    """
    return jsonify({"success":True,"data":None}),200


@zones_bp.route("/zones/<int:zone_id>", methods=["GET"])
def get_zone(zone_id):
    """Returns a single zone by LocationID."""
    return jsonify({"success":True,"data":None}),200


@zones_bp.route("/zones/boroughs", methods=["GET"])
def list_boroughs():
    """Returns a distinct list of borough names."""
    return jsonify({"success":True,"data":None}),200
