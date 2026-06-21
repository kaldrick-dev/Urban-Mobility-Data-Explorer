from flask import Blueprint, request, jsonify
from app.services.analytics_service import (
    trips_by_hour, trips_by_day, trips_by_borough,
    fare_distribution, distance_distribution,
    speed_by_hour, payment_breakdown,
    top_routes, trips_by_zone,
)

analytics_bp = Blueprint("analytics", __name__)

_FILTER_KEYS = [
    "pickup_borough", "rush_hour",
    "date_from", "date_to",
    "min_fare", "max_fare",
    "min_distance", "max_distance",
]

def _filters():
    return {k: request.args.get(k) for k in _FILTER_KEYS}

@analytics_bp.route("/analytics/trips-by-hour")
def by_hour():
    return jsonify({"data": trips_by_hour(_filters())})

@analytics_bp.route("/analytics/trips-by-day")
def by_day():
    return jsonify({"data": trips_by_day(_filters())})

@analytics_bp.route("/analytics/trips-by-borough")
def by_borough():
    return jsonify({"data": trips_by_borough(_filters())})

@analytics_bp.route("/analytics/fare-distribution")
def fare_dist():
    return jsonify({"data": fare_distribution(_filters())})

@analytics_bp.route("/analytics/distance-distribution")
def distance_dist():
    return jsonify({"data": distance_distribution(_filters())})

@analytics_bp.route("/analytics/speed-by-hour")
def speed():
    return jsonify({"data": speed_by_hour(_filters())})

@analytics_bp.route("/analytics/payment-breakdown")
def payment():
    return jsonify({"data": payment_breakdown(_filters())})

@analytics_bp.route("/analytics/top-routes")
def routes():
    limit = int(request.args.get("limit", 8))
    return jsonify({"data": top_routes(_filters(), limit)})

@analytics_bp.route("/analytics/trips-by-zone")
def by_zone():
    return jsonify({"data": trips_by_zone(_filters())})
