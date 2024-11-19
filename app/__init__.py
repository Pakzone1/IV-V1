from flask import Flask
from config import Config
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Create temporary directory for audio files if it doesn't exist
    temp_dir = os.path.join(app.root_path, 'temp')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    from app.routes import main
    app.register_blueprint(main)

    return app 