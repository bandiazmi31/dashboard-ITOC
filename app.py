import flask
import flask_session
from config import Config
from utils.db import init_db
from routes.auth import create_auth_routes
from routes.api_tickets import bp as tickets_bp
from routes.api_handovers import bp as handovers_bp
from routes.api_shifts import bp as shifts_bp
from routes.api_links import bp as links_bp
from routes.api_soc import bp as soc_bp
from routes.api_import import bp as import_bp
from utils.dummy_generator import seed_all
import os

app = flask.Flask(__name__)
app.config.from_object(Config)

# Initialize Flask-Session
flask_session.Session(app)

# Initialize DB connection
try:
    init_db()
except Exception as e:
    print(f"Warning: Database connection issue on startup: {e}")

# Register Blueprints
app.register_blueprint(create_auth_routes())
app.register_blueprint(tickets_bp)
app.register_blueprint(handovers_bp)
app.register_blueprint(shifts_bp)
app.register_blueprint(links_bp)
app.register_blueprint(soc_bp)
app.register_blueprint(import_bp)

@app.route("/")
def index():
    return flask.render_template("index.html")

@app.route("/login")
def login_page():
    return flask.render_template("login.html")

@app.route("/import-soc")
def import_soc_page():
    return flask.render_template("import_soc.html")

# CLI Command to seed database
@app.cli.command("seed-db")
def seed_db_command():
    """Seeds the database with initial dummy data."""
    seed_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
