import threading


class Database:
    def __init__(self):
        self.rooms = {}
        self.room_names = {}
        self.bookings = {}
        self.idempotency = {}
        self.lock = threading.Lock()

    def clear(self):
        with self.lock:
            self.rooms.clear()
            self.room_names.clear()
            self.bookings.clear()
            self.idempotency.clear()


db = Database()
