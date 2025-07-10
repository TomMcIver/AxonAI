import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models and routes
    import models
    import routes
    import api_routes
    
    # Drop and recreate all tables to handle schema changes
    db.drop_all()
    db.create_all()
    
    # Initialize comprehensive dummy data with AI features
    from init_db import init_dummy_users, init_ai_models, init_dummy_classes, init_sample_chat_history, init_student_profiles
    init_dummy_users()
    init_ai_models()
    init_dummy_classes()
    init_sample_chat_history()
    init_student_profiles()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
