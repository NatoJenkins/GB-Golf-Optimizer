"""
Flask application factory for the GB Golf Optimizer web layer.
"""
import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from gbgolf.data import load_config


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Max upload size: 5 MB
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    # Secret key for Flask cookie session (lock/exclude state)
    # In production this should come from an environment variable.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    # Resolve contest_config.json relative to this file (2 levels up = project root)
    config_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "contest_config.json")
    )
    app.config["CONFIG_PATH"] = config_path

    # Load contests at startup so routes don't hit disk on every request
    app.config["CONTESTS"] = load_config(config_path)

    # Apply ProxyFix only in non-testing mode (interferes with test client URL generation)
    if not app.config.get("TESTING"):
        app.wsgi_app = ProxyFix(  # type: ignore[method-assign]
            app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
        )

    from gbgolf.web.routes import bp
    app.register_blueprint(bp)

    return app
