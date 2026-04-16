from flask import Blueprint, request, jsonify
from datetime import datetime
from app.services.booking_service import BookingService

booking_bp = Blueprint("bookings", __name__)
booking_service = BookingService()


def error_response(status, message):
    label = {400: "ValidationError", 404: "NotFoundError", 409: "ConflictError"}.get(status, "Error")
    return jsonify({"error": label, "message": message}), status


@booking_bp.route("/bookings", methods=["POST"])
def create_booking():
    data = request.get_json(silent=True) or {}
    idem_key = request.headers.get("Idempotency-Key")
    booking, err = booking_service.create_booking(
        data.get("roomId"), data.get("title"), data.get("organizerEmail"),
        data.get("startTime"), data.get("endTime"), idempotency_key=idem_key,
    )
    if err:
        return error_response(err[0], err[1])
    return jsonify(booking.to_dict()), 201


@booking_bp.route("/bookings", methods=["GET"])
def list_bookings():
    room_id = request.args.get("roomId")
    from_str = request.args.get("from")
    to_str = request.args.get("to")
    limit = request.args.get("limit", 20, type=int)
    offset = request.args.get("offset", 0, type=int)

    from_time = datetime.fromisoformat(from_str) if from_str else None
    to_time = datetime.fromisoformat(to_str) if to_str else None

    items, total, lim, off = booking_service.list_bookings(room_id, from_time, to_time, limit, offset)
    return jsonify({
        "items": [b.to_dict() for b in items],
        "total": total,
        "limit": lim,
        "offset": off,
    }), 200


@booking_bp.route("/bookings/<booking_id>/cancel", methods=["POST"])
def cancel_booking(booking_id):
    booking, err = booking_service.cancel_booking(booking_id)
    if err:
        return error_response(err[0], err[1])
    return jsonify(booking.to_dict()), 200


@booking_bp.route("/reports/room-utilization", methods=["GET"])
def room_utilization():
    from_str = request.args.get("from")
    to_str = request.args.get("to")
    if not from_str or not to_str:
        return error_response(400, "from and to query parameters are required.")
    try:
        from_time = datetime.fromisoformat(from_str)
        to_time = datetime.fromisoformat(to_str)
    except ValueError:
        return error_response(400, "from and to must be valid ISO-8601 strings.")
    results = booking_service.get_utilization(from_time, to_time)
    return jsonify(results), 200
