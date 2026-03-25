"""
Flask application factory for the GB Golf Optimizer web layer.
"""
import os

import click
from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix

from gbgolf.data import load_config
from gbgolf.db import db


def create_app() -> Flask:
    """Create and configure the Flask application."""
    load_dotenv()  # loads .env into os.environ (no-op if .env missing and vars already set)

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Max upload size: 5 MB
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    # Secret key for Flask cookie session (lock/exclude state)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

    # Database config -- default to SQLite in-memory if DATABASE_URL not set (test/dev fallback)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///:memory:"
    )
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
    }

    # Resolve contest_config.json relative to this file (2 levels up = project root)
    config_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "contest_config.json")
    )
    app.config["CONFIG_PATH"] = config_path

    # Load contests at startup so routes don't hit disk on every request
    app.config["CONTESTS"] = load_config(config_path)

    # Initialize database and migrations
    db.init_app(app)
    Migrate(app, db)

    # Apply ProxyFix only in non-testing mode (interferes with test client URL generation)
    if not app.config.get("TESTING"):
        app.wsgi_app = ProxyFix(  # type: ignore[method-assign]
            app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
        )

    from gbgolf.web.routes import bp
    app.register_blueprint(bp)

    @app.cli.command("fetch-projections")
    def fetch_projections_cmd():
        """Fetch player projections from DataGolf API and store in database."""
        from gbgolf.fetcher import run_fetch
        result = run_fetch()
        click.echo(result)

    return app
