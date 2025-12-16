"""
Simple rate limiter using database storage for production hardening.
Limits: 30 requests per 5 minutes per user on tutor endpoints.
"""
import functools
from datetime import datetime, timedelta
from flask import session, jsonify, request
from app import db

RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW_SECONDS = 300  # 5 minutes

class RateLimitEntry(db.Model):
    __tablename__ = 'rate_limit_entry'
    
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(128), nullable=False, index=True)
    endpoint = db.Column(db.String(100), nullable=False)
    request_count = db.Column(db.Integer, default=1)
    window_start = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_rate_limit_identifier_endpoint', 'identifier', 'endpoint'),
    )

def _get_client_identifier():
    """Get identifier for rate limiting: user_id if logged in, else IP address"""
    user_id = session.get('user_id')
    if user_id:
        return f'user:{user_id}'
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip:
        ip = ip.split(',')[0].strip()
    return f'ip:{ip or "unknown"}'

def rate_limit(limit=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW_SECONDS):
    """Decorator to apply rate limiting to an endpoint (works for both authenticated and anonymous)"""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            identifier = _get_client_identifier()
            endpoint = request.endpoint or 'unknown'
            now = datetime.utcnow()
            window_cutoff = now - timedelta(seconds=window)
            
            entry = RateLimitEntry.query.filter_by(
                identifier=identifier,
                endpoint=endpoint
            ).first()
            
            if entry:
                if entry.window_start < window_cutoff:
                    entry.request_count = 1
                    entry.window_start = now
                else:
                    if entry.request_count >= limit:
                        remaining_seconds = window - (now - entry.window_start).total_seconds()
                        return jsonify({
                            'success': False,
                            'error': 'Rate limit exceeded',
                            'retry_after_seconds': int(remaining_seconds)
                        }), 429
                    entry.request_count += 1
            else:
                entry = RateLimitEntry(
                    identifier=identifier,
                    endpoint=endpoint,
                    request_count=1,
                    window_start=now
                )
                db.session.add(entry)
            
            try:
                db.session.commit()
            except:
                db.session.rollback()
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

def cleanup_old_entries():
    """Cleanup rate limit entries older than 1 hour"""
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    RateLimitEntry.query.filter(RateLimitEntry.window_start < one_hour_ago).delete()
    db.session.commit()
