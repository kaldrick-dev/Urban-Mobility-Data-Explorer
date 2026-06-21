from flask import Blueprint, request, jsonify
from app.services.trip_service import get_trips, get_trip, get_trip_stats

trips_bp = Blueprint("trips", __name__)

_FILTER_KEYS = [
    "pickup_borough", "rush_hour",
    "date_from", "date_to",
    "min_fare", "max_fare",
    "min_distance", "max_distance",
]

@trips_bp.route("/trips")
def trips():
    filters    = {k: request.args.get(k) for k in _FILTER_KEYS}
    pagination = {"page": request.args.get("page", 1), "per_page": request.args.get("per_page", 50)}
    sort       = {"sort_by": request.args.get("sort_by"), "sort_dir": request.args.get("sort_dir")}
    return jsonify({"data": get_trips(filters, pagination, sort)})

@trips_bp.route("/trips/<int:trip_id>")
def trip(trip_id):
    result = get_trip(trip_id)
    if result is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"data": result})

@trips_bp.route("/trip/stats")
def trip_stats():
    filters = {k: request.args.get(k) for k in _FILTER_KEYS}
    return jsonify({"data": get_trip_stats(filters)})