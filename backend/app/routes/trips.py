from flask import Blueprint, jsonify, request
from app.services.trip_service import get_trips, get_trip_by_id, get_trip_stats

trips_bp = Blueprint("trips", __name__)


@trips_bp.route("/trips", methods=["GET"])
def list_trips():
    """
    Paginated trip list with optional filters.

    Query params:
      page, per_page
      from_date, to_date          ISO datetime strings
      pickup_borough, dropoff_borough
      pickup_zone_id, dropoff_zone_id
      min_distance, max_distance
      min_fare, max_fare
      payment_type                1=Credit 2=Cash 3=No charge 4=Dispute
      time_of_day                 morning|afternoon|evening|night
      is_rush_hour                true|false
      sort_by                     pickup_datetime|total_amount|trip_distance|duration_minutes
      sort_order                  asc|desc
    """
    return jsonify({"success": True, "data": None}), 200


@trips_bp.route("/trips/stats", methods=["GET"])
def trip_stats():
    """
    Aggregate statistics over all trips (or filtered subset).

    Accepts same date/location filters as GET /trips.

    Response fields:
      total_trips, avg_fare, avg_distance, avg_duration_minutes,
      avg_speed_mph, avg_tip_amount, avg_passenger_count, total_revenue
    """
    return jsonify({"success": True, "data": None}), 200


@trips_bp.route("/trips/<int:trip_id>", methods=["GET"])
def get_trip(trip_id):
    """Returns a single trip record by ID."""
    return jsonify({"success": True, "data": None}), 200
