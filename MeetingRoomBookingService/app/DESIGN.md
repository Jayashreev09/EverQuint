# DESIGN.md — Meeting Room Booking Service

## Project Structure

```
app/
  __init__.py
  models/models.py     # Room, Booking, IdempotencyRecord
  persistence/database.py
  services/
    room_service.py    # Room business logic
    booking_service.py # Booking business logic
  controllers/
    room_controller.py    # /rooms endpoints
    booking_controller.py # /bookings + /reports endpoints
tests/
  test_api.py
```

## Data Model

- **Room**: `id`, `name` (unique, case-insensitive), `capacity`, `floor`, `amenities[]`
- **Booking**: `id`, `roomId`, `title`, `organizerEmail`, `startTime`, `endTime`, `status` (confirmed | cancelled)
- **IdempotencyRecord**: `(key, organizerEmail)` → `bookingId`, `responseBody`

All stored in-memory via a singleton `Database` object with dict-based tables.

## How Overlaps Are Enforced

During `create_booking`, inside a single `threading.Lock` critical section:
1. All existing **confirmed** bookings for the same `roomId` are scanned.
2. Two intervals overlap if `existing.start < new.end AND existing.end > new.start`.
3. If overlap found → 409 Conflict.
4. Cancelled bookings are excluded from overlap checks, so cancelling frees the slot.

## Error Handling Strategy

All errors return a consistent JSON shape:
```json
{ "error": "<ErrorType>", "message": "<details>" }
```
- **400** → `ValidationError` (bad input, business rule violation, grace period)
- **404** → `NotFoundError` (unknown room or booking)
- **409** → `ConflictError` (overlapping booking)

Validation is performed in the service layer, not in controllers.

## How Idempotency Is Implemented

- Client sends `Idempotency-Key` header on `POST /bookings`.
- Keys are scoped per `organizerEmail` (composite key: `(idempotencyKey, organizerEmail)`).
- On first request: booking is created and the `(key, email) → bookingId` mapping is stored.
- On subsequent requests with the same key+email: the original booking is returned (no duplicate created).
- The idempotency store lives in the same `Database` singleton (in production, this would be a DB table with a unique constraint).

## How Concurrency Issues Are Handled

- A single `threading.Lock` guards all mutations (create room, create booking, cancel booking).
- The overlap check + insert happens atomically inside the lock, preventing double-booking under concurrent requests.
- **Trade-off**: This is a coarse-grained lock. In production, you'd use:
  - DB-level row locking or `SELECT ... FOR UPDATE` on the room.
  - A unique constraint on `(idempotencyKey, organizerEmail)` with retry on conflict.
  - Optimistic concurrency with version columns.

## How Utilization Is Calculated

```
Utilization = totalBookedHours(from, to) / totalBusinessHours(from, to)
```

- **Business hours**: Mon–Fri, 08:00–20:00 (12h/day).
- **totalBusinessHours**: Sum of business-hour windows that fall within `[from, to]` across all weekdays in range.
- **totalBookedHours**: For each confirmed booking in the room, compute the overlap between `[booking.start, booking.end]` and `[from, to]`, sum the hours.
- Edge cases handled:
  - Booking starts before `from` → only the portion after `from` is counted.
  - Booking ends after `to` → only the portion before `to` is counted.
  - No bookings → 0% utilization.
