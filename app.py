import os
import logging
from urllib.parse import urlparse
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Successfully loaded .env file")
except ImportError:
    print("python-dotenv not installed. Using system environment variables only.")

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)

from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.secret_key = os.environ.get("SESSION_SECRET")
if not app.secret_key:
    raise ValueError("SESSION_SECRET environment variable must be set for security")

if os.environ.get('DATABASE_URL'):
    print("DATABASE_URL configured successfully")
if os.environ.get('SESSION_SECRET'):
    print("SESSION_SECRET configured successfully")

def configure_database():
    """Configure database connection with Supabase/PostgreSQL support."""
    supabase_url = os.environ.get("SUPABASE_DB_URL")
    database_url = os.environ.get("DATABASE_URL")
    
    if supabase_url:
        db_url = supabase_url
        print("Using Supabase PostgreSQL database")
    elif database_url:
        db_url = database_url
        print("Using DATABASE_URL PostgreSQL database")
    else:
        db_url = "sqlite:///school_management.db"
        print("Warning: No PostgreSQL URL set. Using SQLite fallback: sqlite:///school_management.db")
        return db_url, {}
    
    if db_url.startswith('postgresql://') or db_url.startswith('postgres://'):
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
        if 'sslmode=' not in db_url:
            separator = '&' if '?' in db_url else '?'
            db_url = f"{db_url}{separator}sslmode=require"
        
        try:
            parsed = urlparse(db_url)
            host = parsed.hostname or 'unknown'
            print(f"PostgreSQL host: {host}")
        except Exception:
            print("PostgreSQL connection configured")
        
        try:
            import psycopg2
            test_conn = psycopg2.connect(db_url)
            test_conn.close()
            print("PostgreSQL connection successful")
        except Exception as e:
            print(f"PostgreSQL connection test failed: {e}")
            print("Will attempt connection at runtime...")
    
    engine_options = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
    }
    
    return db_url, engine_options

database_url, engine_options = configure_database()

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options if engine_options else {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
    print("Using PostgreSQL database")
else:
    print("Using SQLite database")

db.init_app(app)

USE_LOCAL_SQLITE_AGENTS = os.environ.get("USE_LOCAL_SQLITE_AGENTS", "false").lower() == "true"
USE_LOCAL_ML = os.environ.get("USE_LOCAL_ML", "false").lower() == "true"

print(f"Feature flags: USE_LOCAL_SQLITE_AGENTS={USE_LOCAL_SQLITE_AGENTS}, USE_LOCAL_ML={USE_LOCAL_ML}")

with app.app_context():
    import models
    
    import routes
    import api_routes
    
    db.create_all()
    
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        try:
            from scheduler_config import init_scheduler
            scheduler = init_scheduler(app)
            print("Big AI Coordinator scheduler initialized")
        except Exception as e:
            print(f"Warning: Could not initialize scheduler: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
