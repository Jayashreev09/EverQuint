import pytest
from app import create_app
from app.persistence.database import db


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    db.clear()
    with app.test_client() as c:
        yield c
    db.clear()


def create_room(client, name="Board Room", capacity=10, floor=1, amenities=None):
    return client.post("/rooms", json={
        "name": name, "capacity": capacity, "floor": floor,
        "amenities": amenities or ["projector"],
    })


def create_booking(client, room_id, start="2026-04-20T09:00:00", end="2026-04-20T10:00:00",
                    title="Standup", email="a@test.com", idem_key=None):
    headers = {"Idempotency-Key": idem_key} if idem_key else {}
    return client.post("/bookings", json={
        "roomId": room_id, "title": title, "organizerEmail": email,
        "startTime": start, "endTime": end,
    }, headers=headers)


class TestCreateRoom:
    def test_success(self, client):
        res = create_room(client)
        assert res.status_code == 201
        data = res.get_json()
        assert data["name"] == "Board Room"
        assert data["capacity"] == 10
        assert "id" in data

    def test_duplicate_name_case_insensitive(self, client):
        create_room(client, name="Alpha")
        res = create_room(client, name="alpha")
        assert res.status_code == 400
        assert "already exists" in res.get_json()["message"]

    def test_invalid_capacity(self, client):
        res = create_room(client, capacity=0)
        assert res.status_code == 400


class TestListRooms:
    def test_filter_by_min_capacity(self, client):
        create_room(client, name="Small", capacity=2)
        create_room(client, name="Big", capacity=20)
        res = client.get("/rooms?minCapacity=10")
        assert len(res.get_json()) == 1
        assert res.get_json()[0]["name"] == "Big"

    def test_filter_by_amenity(self, client):
        create_room(client, name="A", amenities=["whiteboard"])
        create_room(client, name="B", amenities=["projector"])
        res = client.get("/rooms?amenity=whiteboard")
        assert len(res.get_json()) == 1


class TestCreateBooking:
    def test_happy_path(self, client):
        room = create_room(client).get_json()
        res = create_booking(client, room["id"])
        assert res.status_code == 201
        assert res.get_json()["status"] == "confirmed"

    def test_start_after_end(self, client):
        room = create_room(client).get_json()
        res = create_booking(client, room["id"], start="2026-04-20T11:00:00", end="2026-04-20T10:00:00")
        assert res.status_code == 400
        assert "before" in res.get_json()["message"]

    def test_duration_too_short(self, client):
        room = create_room(client).get_json()
        res = create_booking(client, room["id"], start="2026-04-20T09:00:00", end="2026-04-20T09:10:00")
        assert res.status_code == 400
        assert "duration" in res.get_json()["message"].lower()

    def test_duration_too_long(self, client):
        room = create_room(client).get_json()
        res = create_booking(client, room["id"], start="2026-04-20T09:00:00", end="2026-04-20T14:00:00")
        assert res.status_code == 400

    def test_outside_business_hours(self, client):
        room = create_room(client).get_json()
        res = create_booking(client, room["id"], start="2026-04-20T07:00:00", end="2026-04-20T08:00:00")
        assert res.status_code == 400
        assert "08:00-20:00" in res.get_json()["message"]

    def test_weekend_rejected(self, client):
        room = create_room(client).get_json()
        res = create_booking(client, room["id"], start="2026-04-18T09:00:00", end="2026-04-18T10:00:00")
        assert res.status_code == 400
        assert "Mon-Fri" in res.get_json()["message"]

    def test_unknown_room_404(self, client):
        res = create_booking(client, "nonexistent-id")
        assert res.status_code == 404

    def test_overlap_conflict_409(self, client):
        room = create_room(client).get_json()
        create_booking(client, room["id"], start="2026-04-20T09:00:00", end="2026-04-20T10:00:00")
        res = create_booking(client, room["id"], start="2026-04-20T09:30:00", end="2026-04-20T10:30:00")
        assert res.status_code == 409

    def test_adjacent_bookings_no_overlap(self, client):
        room = create_room(client).get_json()
        create_booking(client, room["id"], start="2026-04-20T09:00:00", end="2026-04-20T10:00:00")
        res = create_booking(client, room["id"], start="2026-04-20T10:00:00", end="2026-04-20T11:00:00")
        assert res.status_code == 201


class TestIdempotency:
    def test_same_key_returns_same_booking(self, client):
        room = create_room(client).get_json()
        r1 = create_booking(client, room["id"], idem_key="key-1", email="a@test.com")
        r2 = create_booking(client, room["id"], idem_key="key-1", email="a@test.com")
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.get_json()["id"] == r2.get_json()["id"]

    def test_different_key_creates_different_booking(self, client):
        room = create_room(client).get_json()
        r1 = create_booking(client, room["id"], idem_key="key-1", email="a@test.com",
                            start="2026-04-20T09:00:00", end="2026-04-20T10:00:00")
        r2 = create_booking(client, room["id"], idem_key="key-2", email="a@test.com",
                            start="2026-04-20T10:00:00", end="2026-04-20T11:00:00")
        assert r1.get_json()["id"] != r2.get_json()["id"]


class TestListBookings:
    def test_pagination(self, client):
        room = create_room(client).get_json()
        for h in range(9, 14):
            create_booking(client, room["id"],
                           start=f"2026-04-20T{h:02d}:00:00",
                           end=f"2026-04-20T{h+1:02d}:00:00")
        res = client.get("/bookings?limit=2&offset=0")
        data = res.get_json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0

    def test_filter_by_room(self, client):
        r1 = create_room(client, name="R1").get_json()
        r2 = create_room(client, name="R2").get_json()
        create_booking(client, r1["id"])
        create_booking(client, r2["id"], start="2026-04-20T11:00:00", end="2026-04-20T12:00:00")
        res = client.get(f"/bookings?roomId={r1['id']}")
        assert res.get_json()["total"] == 1


class TestCancelBooking:
    def test_cancel_success(self, client):
        room = create_room(client).get_json()
        booking = create_booking(client, room["id"],
                                 start="2026-04-20T09:00:00", end="2026-04-20T10:00:00").get_json()
        res = client.post(f"/bookings/{booking['id']}/cancel")
        assert res.status_code == 200
        assert res.get_json()["status"] == "cancelled"

    def test_cancel_already_cancelled_is_noop(self, client):
        room = create_room(client).get_json()
        booking = create_booking(client, room["id"],
                                 start="2026-04-20T09:00:00", end="2026-04-20T10:00:00").get_json()
        client.post(f"/bookings/{booking['id']}/cancel")
        res = client.post(f"/bookings/{booking['id']}/cancel")
        assert res.status_code == 200
        assert res.get_json()["status"] == "cancelled"

    def test_cancelled_booking_does_not_block_new(self, client):
        room = create_room(client).get_json()
        b = create_booking(client, room["id"],
                           start="2026-04-20T09:00:00", end="2026-04-20T10:00:00").get_json()
        client.post(f"/bookings/{b['id']}/cancel")
        res = create_booking(client, room["id"],
                             start="2026-04-20T09:00:00", end="2026-04-20T10:00:00",
                             email="b@test.com")
        assert res.status_code == 201

    def test_cancel_nonexistent_404(self, client):
        res = client.post("/bookings/fake-id/cancel")
        assert res.status_code == 404


class TestUtilizationReport:
    def test_basic_utilization(self, client):
        room = create_room(client).get_json()
        create_booking(client, room["id"], start="2026-04-20T09:00:00", end="2026-04-20T11:00:00")
        res = client.get("/reports/room-utilization?from=2026-04-20T00:00:00&to=2026-04-20T23:59:59")
        data = res.get_json()
        assert len(data) == 1
        assert data[0]["totalBookingHours"] == 2.0
        assert data[0]["utilizationPercent"] == 0.17

    def test_no_bookings_zero_utilization(self, client):
        create_room(client)
        res = client.get("/reports/room-utilization?from=2026-04-20T00:00:00&to=2026-04-20T23:59:59")
        data = res.get_json()
        assert data[0]["totalBookingHours"] == 0.0
        assert data[0]["utilizationPercent"] == 0.0

    def test_partial_overlap_with_range(self, client):
        room = create_room(client).get_json()
        create_booking(client, room["id"], start="2026-04-20T09:00:00", end="2026-04-20T11:00:00")
        res = client.get("/reports/room-utilization?from=2026-04-20T10:00:00&to=2026-04-20T20:00:00")
        data = res.get_json()
        assert data[0]["totalBookingHours"] == 1.0

    def test_missing_params_400(self, client):
        res = client.get("/reports/room-utilization")
        assert res.status_code == 400


class TestErrorFormat:
    def test_consistent_error_json(self, client):
        res = create_room(client, capacity=-1)
        data = res.get_json()
        assert "error" in data
        assert "message" in data