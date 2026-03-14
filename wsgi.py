"""Gunicorn / WSGI entry point for the GB Golf Optimizer."""
from gbgolf.web import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
