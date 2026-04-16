from flask import Flask
from app.controllers.room_controller import room_bp
from app.controllers.booking_controller import booking_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(room_bp)
    app.register_blueprint(booking_bp)
    return app


if __name__ == "__main__":
    create_app().run(debug=True)
