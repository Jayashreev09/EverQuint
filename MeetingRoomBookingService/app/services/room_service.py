from app.models.models import Room
from app.persistence.database import db


class RoomService:
    def create_room(self, name, capacity, floor, amenities):
        errors = []
        if not name or not isinstance(name, str):
            errors.append("name is required and must be a string.")
        if not isinstance(capacity, int) or capacity < 1:
            errors.append("capacity must be a positive integer (>=1).")
        if not isinstance(floor, int):
            errors.append("floor must be an integer.")
        if amenities is not None and not isinstance(amenities, list):
            errors.append("amenities must be an array of strings.")
        if errors:
            return None, errors

        with db.lock:
            if name.lower() in db.room_names:
                return None, ["A room with this name already exists (case-insensitive)."]
            room = Room(name, capacity, floor, amenities or [])
            db.rooms[room.id] = room
            db.room_names[name.lower()] = room.id
        return room, None

    def list_rooms(self, min_capacity=None, amenity=None):
        with db.lock:
            rooms = list(db.rooms.values())
        if min_capacity is not None:
            rooms = [r for r in rooms if r.capacity >= min_capacity]
        if amenity is not None:
            amenity_lower = amenity.lower()
            rooms = [r for r in rooms if amenity_lower in [a.lower() for a in r.amenities]]
        return rooms

    def get_room(self, room_id):
        with db.lock:
            return db.rooms.get(room_id)
