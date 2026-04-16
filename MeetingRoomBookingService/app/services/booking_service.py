from datetime import datetime, timedelta
from app.models.models import Booking, IdempotencyRecord
from app.persistence.database import db


class BookingService:
    MIN_DURATION = timedelta(minutes=15)
    MAX_DURATION = timedelta(hours=4)
    BUSINESS_START = 8
    BUSINESS_END = 20
    BUSINESS_DAYS = range(0, 5)

    def create_booking(self, room_id, title, organizer_email, start_time_str, end_time_str, idempotency_key=None):
        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
        except (ValueError, TypeError):
            return None, (400, "startTime and endTime must be valid ISO-8601 strings.")

        errors = self._validate_booking(room_id, title, organizer_email, start_time, end_time)
        if errors:
            return None, (400, errors)

        with db.lock:
            if idempotency_key:
                idem_record = db.idempotency.get((idempotency_key, organizer_email))
                if idem_record:
                    existing = db.bookings.get(idem_record.booking_id)
                    if existing:
                        return existing, None

            if room_id not in db.rooms:
                return None, (404, "Room not found.")

            if self._has_overlap(room_id, start_time, end_time):
                return None, (409, "Overlapping confirmed booking exists for this room.")

            booking = Booking(room_id, title, organizer_email, start_time, end_time)
            db.bookings[booking.id] = booking

            if idempotency_key:
                db.idempotency[(idempotency_key, organizer_email)] = IdempotencyRecord(
                    idempotency_key, organizer_email, booking.id, booking.to_dict()
                )

        return booking, None

    def list_bookings(self, room_id=None, from_time=None, to_time=None, limit=20, offset=0):
        with db.lock:
            bookings = list(db.bookings.values())

        if room_id:
            bookings = [b for b in bookings if b.room_id == room_id]
        if from_time:
            bookings = [b for b in bookings if b.end_time > from_time]
        if to_time:
            bookings = [b for b in bookings if b.start_time < to_time]

        bookings.sort(key=lambda b: b.start_time)
        total = len(bookings)
        items = bookings[offset:offset + limit]
        return items, total, limit, offset

    def cancel_booking(self, booking_id):
        with db.lock:
            booking = db.bookings.get(booking_id)
            if not booking:
                return None, (404, "Booking not found.")

            if booking.status == "cancelled":
                return booking, None

            now = datetime.utcnow()
            if booking.start_time - now < timedelta(hours=1):
                return None, (400, "Booking can only be cancelled up to 1 hour before startTime.")

            booking.status = "cancelled"
        return booking, None

    def get_utilization(self, from_time, to_time):
        with db.lock:
            rooms = list(db.rooms.values())
            bookings = [b for b in db.bookings.values() if b.status == "confirmed"]

        results = []
        total_biz_hours = self._total_business_hours(from_time, to_time)

        for room in rooms:
            room_bookings = [b for b in bookings if b.room_id == room.id]
            booked_hours = 0.0
            for b in room_bookings:
                overlap_start = max(b.start_time, from_time)
                overlap_end = min(b.end_time, to_time)
                if overlap_start < overlap_end:
                    booked_hours += (overlap_end - overlap_start).total_seconds() / 3600.0

            utilization = round(booked_hours / total_biz_hours, 2) if total_biz_hours > 0 else 0.0
            results.append({
                "roomId": room.id,
                "roomName": room.name,
                "totalBookingHours": round(booked_hours, 2),
                "utilizationPercent": utilization,
            })
        return results

    def _validate_booking(self, room_id, title, organizer_email, start_time, end_time):
        errors = []
        if not room_id:
            errors.append("roomId is required.")
        if not title:
            errors.append("title is required.")
        if not organizer_email:
            errors.append("organizerEmail is required.")
        if start_time >= end_time:
            errors.append("startTime must be before endTime.")
            return "; ".join(errors)

        duration = end_time - start_time
        if duration < self.MIN_DURATION or duration > self.MAX_DURATION:
            errors.append("Booking duration must be between 15 minutes and 4 hours.")

        if start_time.weekday() not in self.BUSINESS_DAYS or end_time.weekday() not in self.BUSINESS_DAYS:
            errors.append("Bookings only allowed Mon-Fri.")
        if start_time.hour < self.BUSINESS_START or end_time.hour > self.BUSINESS_END or \
           (end_time.hour == self.BUSINESS_END and end_time.minute > 0):
            errors.append("Bookings only allowed 08:00-20:00.")
        if start_time.date() != end_time.date():
            errors.append("Booking must start and end on the same day.")

        return "; ".join(errors) if errors else None

    def _has_overlap(self, room_id, start_time, end_time, exclude_id=None):
        for b in db.bookings.values():
            if b.room_id == room_id and b.status == "confirmed" and b.id != exclude_id:
                if b.start_time < end_time and b.end_time > start_time:
                    return True
        return False

    def _total_business_hours(self, from_dt, to_dt):
        total = 0.0
        current = from_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = to_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        while current <= end_date:
            if current.weekday() in self.BUSINESS_DAYS:
                day_start = current.replace(hour=self.BUSINESS_START)
                day_end = current.replace(hour=self.BUSINESS_END)
                window_start = max(day_start, from_dt)
                window_end = min(day_end, to_dt)
                if window_start < window_end:
                    total += (window_end - window_start).total_seconds() / 3600.0
            current += timedelta(days=1)
        return total
