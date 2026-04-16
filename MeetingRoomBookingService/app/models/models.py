import uuid
from datetime import datetime


class Room:
    def __init__(self, name, capacity, floor, amenities=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.capacity = capacity
        self.floor = floor
        self.amenities = amenities or []

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "capacity": self.capacity,
            "floor": self.floor,
            "amenities": self.amenities,
        }


class Booking:
    def __init__(self, room_id, title, organizer_email, start_time, end_time):
        self.id = str(uuid.uuid4())
        self.room_id = room_id
        self.title = title
        self.organizer_email = organizer_email
        self.start_time = start_time
        self.end_time = end_time
        self.status = "confirmed"
        self.created_at = datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "roomId": self.room_id,
            "title": self.title,
            "organizerEmail": self.organizer_email,
            "startTime": self.start_time.isoformat(),
            "endTime": self.end_time.isoformat(),
            "status": self.status,
        }


class IdempotencyRecord:
    def __init__(self, key, organizer_email, booking_id, response_body):
        self.key = key
        self.organizer_email = organizer_email
        self.booking_id = booking_id
        self.response_body = response_body
