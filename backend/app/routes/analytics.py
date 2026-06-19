from flask import Blueprint, jsonify, request
from app.services.analytics_service import (
    get_busiest_zones,
    get_overall_summary,
)

analytics_bp = Blueprint("analytics", __name__)


def _build_filters():
    return {
        "start_date": request.args.get("start_date"),
        "end_date": request.args.get("end_date"),
        "pickup_borough": request.args.get("pickup_borough"),
    }


@analytics_bp.route("/analytics/metrics", methods=["GET"])
def metrics():
    filters = _build_filters()
    summary = get_overall_summary(filters)
    return jsonify({"success": True, "data": summary}), 200


@analytics_bp.route("/analytics/busiest-zones", methods=["GET"])
def busiest_zones():
    filters = _build_filters()
    metric = request.args.get("metric", "trip_count")
    limit = int(request.args.get("limit", 20))
    ranked = get_busiest_zones(filters, metric=metric, limit=limit)
    return jsonify({"success": True, "data": ranked}), 200
