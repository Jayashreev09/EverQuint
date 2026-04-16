from flask import Blueprint, request, jsonify
from app.services.room_service import RoomService

room_bp = Blueprint("rooms", __name__)
room_service = RoomService()


def error_response(status, message):
    return jsonify({"error": "ValidationError" if status == 400 else "ConflictError" if status == 409 else "NotFoundError", "message": message}), status


@room_bp.route("/rooms", methods=["POST"])
def create_room():
    data = request.get_json(silent=True) or {}
    room, errors = room_service.create_room(
        data.get("name"), data.get("capacity"), data.get("floor", 0), data.get("amenities")
    )
    if errors:
        return error_response(400, "; ".join(errors))
    return jsonify(room.to_dict()), 201


@room_bp.route("/rooms", methods=["GET"])
def list_rooms():
    min_cap = request.args.get("minCapacity", type=int)
    amenity = request.args.get("amenity")
    rooms = room_service.list_rooms(min_capacity=min_cap, amenity=amenity)
    return jsonify([r.to_dict() for r in rooms]), 200
