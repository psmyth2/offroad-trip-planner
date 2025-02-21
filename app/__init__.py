import os
import sys
import logging
from flask import Flask
from flask_cors import CORS

# ✅ Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# ✅ Set log file path inside a writable directory
LOG_FILE_PATH = os.path.join(LOG_DIR, "app.log")

# ✅ Configure Logging Once for Entire App
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),  # ✅ Save logs to a file
        logging.StreamHandler(sys.stdout)  # ✅ Print logs to console
    ]
)

# ✅ Create Flask App
def create_app():
    """Flask application factory."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'supersecretkey'
    CORS(app)

    # ✅ Log startup message
    logging.info("🚀 Flask App Started. Logging initialized.")

    # Import blueprints and register them
    from app.routes import routes
    app.register_blueprint(routes)

    return app
