from flask import Blueprint, jsonify, request
from app.services.trip_service import get_trips, get_trip_by_id, get_trip_stats

trips_bp = Blueprint("trips", __name__)


def _extract_filters():
    return {
        "start_date": request.args.get("from_date") or request.args.get("start_date"),
        "end_date": request.args.get("to_date") or request.args.get("end_date"),
        "pickup_borough": request.args.get("pickup_borough"),
        "dropoff_borough": request.args.get("dropoff_borough"),
        "pickup_zone_id": request.args.get("pickup_zone_id"),
        "dropoff_zone_id": request.args.get("dropoff_zone_id"),
        "min_distance": request.args.get("min_distance"),
        "max_distance": request.args.get("max_distance"),
        "min_fare": request.args.get("min_fare"),
        "max_fare": request.args.get("max_fare"),
        "payment_type": request.args.get("payment_type"),
        "time_of_day": request.args.get("time_of_day"),
        "is_rush_hour": request.args.get("is_rush_hour"),
    }


def _extract_pagination():
    return {
        "page": request.args.get("page", 1),
        "per_page": request.args.get("per_page", 25),
    }


def _extract_sort():
    return {
        "sort_by": request.args.get("sort_by", "pickup_datetime"),
        "sort_order": request.args.get("sort_order", "desc"),
    }


@trips_bp.route("/trips", methods=["GET"])
def list_trips():
    filters = _extract_filters()
    pagination = _extract_pagination()
    sort = _extract_sort()
    page_data = get_trips(filters, pagination, sort)
    return jsonify({"success": True, "data": page_data}), 200


@trips_bp.route("/trips/stats", methods=["GET"])
def trip_stats():
    filters = _extract_filters()
    stats = get_trip_stats(filters)
    return jsonify({"success": True, "data": stats}), 200


@trips_bp.route("/trips/<int:trip_id>", methods=["GET"])
def get_trip(trip_id):
    trip = get_trip_by_id(trip_id)
    if not trip:
        return jsonify({"success": False, "message": "Trip not found."}), 404
    return jsonify({"success": True, "data": trip}), 200
