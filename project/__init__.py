# project/__init__.py
from flask import Flask
from .views import main
from .auth import auth


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["SECRET_KEY"] = "dev-secret-change-me"  # change in production

    # Blueprints
    from .views import main
    from .auth import auth
    app.register_blueprint(main)
    app.register_blueprint(auth)

    return app
