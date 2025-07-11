import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Successfully loaded .env file")
except ImportError:
    print("python-dotenv not installed. Using system environment variables only.")

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Debug: Print environment variables
print(f"DATABASE_URL from env: {os.environ.get('DATABASE_URL')}")
print(f"SESSION_SECRET from env: {os.environ.get('SESSION_SECRET')}")

# Configure the database with automatic fallback
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    # Fallback to SQLite for development if no DATABASE_URL is set
    database_url = "sqlite:///school_management.db"
    print("Warning: DATABASE_URL not set. Using SQLite fallback: sqlite:///school_management.db")
else:
    # Test PostgreSQL connection and fallback to SQLite if it fails
    if database_url.startswith('postgresql://'):
        try:
            import psycopg2
            # Test the connection
            test_conn = psycopg2.connect(database_url)
            test_conn.close()
            print("PostgreSQL connection successful")
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}")
            print("Falling back to SQLite for development")
            database_url = "sqlite:///school_management.db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

print(f"Final DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Initialize the app with the extension
db.init_app(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
