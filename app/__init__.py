import os
import sys
import logging
from flask import Flask
from flask_cors import CORS

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, "app.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),  # ✅ Save logs to a file
        logging.StreamHandler(sys.stdout)  # ✅ Print logs to console
    ]
)

#create flask app
def create_app():
    """Flask application factory."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'supersecretkey'
    CORS(app)

    logging.info("🚀 Flask App Started. Logging initialized.")

    #import blueprints and register them
    from app.routes import routes
    app.register_blueprint(routes)

    return app
