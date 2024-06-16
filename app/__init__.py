from flask import Flask
import os


def create_app():
    app = Flask(__name__)

    # Автогенерация секретного ключа
    secret_key = os.urandom(24).hex()
    app.secret_key = secret_key

    from .views import main

    app.register_blueprint(main)

    return app
