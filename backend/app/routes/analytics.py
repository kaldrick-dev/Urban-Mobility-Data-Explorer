from flask import Blueprint, jsonify, request
from app.services.analytics_service import (
    get_trips_by_hour,
    get_trips_by_day,
    get_trips_by_borough,
    get_fare_distribution,
    get_top_routes,
    get_payment_breakdown,
    get_speed_by_hour,
    get_distance_distribution,
)

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics/trips-by-hour", methods=["GET"])
def trips_by_hour():
    """
    Trip count and avg fare grouped by hour of day (0–23).

    Query params: from_date, to_date, pickup_borough
    """
    pass


@analytics_bp.route("/analytics/trips-by-day", methods=["GET"])
def trips_by_day():
    """
    Trip count grouped by calendar date.

    Query params: from_date, to_date, pickup_borough
    """
    pass


@analytics_bp.route("/analytics/trips-by-borough", methods=["GET"])
def trips_by_borough():
    """
    Trip count and total revenue grouped by pickup borough.

    Query params: from_date, to_date
    """
    pass


@analytics_bp.route("/analytics/fare-distribution", methods=["GET"])
def fare_distribution():
    """
    Histogram data for total_amount bucketed into ranges.

    Query params: from_date, to_date, pickup_borough, bucket_size (default 5)
    """
    pass


@analytics_bp.route("/analytics/top-routes", methods=["GET"])
def top_routes():
    """
    Most frequent pickup → dropoff zone pairs.

    Query params: from_date, to_date, limit (default 20)
    """
    pass


@analytics_bp.route("/analytics/payment-breakdown", methods=["GET"])
def payment_breakdown():
    """
    Trip count and revenue split by payment type.

    Query params: from_date, to_date
    """
    pass


@analytics_bp.route("/analytics/speed-by-hour", methods=["GET"])
def speed_by_hour():
    """
    Average trip speed (mph) grouped by hour of day — reveals congestion patterns.

    Query params: from_date, to_date, pickup_borough
    """
    pass


@analytics_bp.route("/analytics/distance-distribution", methods=["GET"])
def distance_distribution():
    """
    Histogram data for trip_distance bucketed into ranges.

    Query params: from_date, to_date, pickup_borough, bucket_size (default 1)
    """
    pass
