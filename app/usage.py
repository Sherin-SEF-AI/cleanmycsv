import redis
from fastapi import Request, HTTPException
from datetime import datetime, timedelta
from typing import Dict
from app.config import settings
import hashlib

# Initialize Redis client
redis_client = redis.from_url(settings.REDIS_URL)

def get_client_identifier(request: Request) -> str:
    """Create unique ID for anonymous users using IP + User-Agent"""
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    # Create a hash of the user agent for privacy
    user_agent_hash = hashlib.md5(user_agent.encode()).hexdigest()[:8]
    
    return f"anon:{client_ip}:{user_agent_hash}"

def check_anonymous_usage(request: Request) -> Dict:
    """Check anonymous user's remaining free cleanings"""
    client_id = get_client_identifier(request)
    current_month = datetime.now().strftime("%Y-%m")
    usage_key = f"usage:{client_id}:{current_month}"
    
    current_usage = redis_client.get(usage_key)
    current_usage = int(current_usage) if current_usage else 0
    
    return {
        "used": current_usage,
        "remaining": max(0, 3 - current_usage),
        "needs_signup": current_usage >= 3
    }

def increment_anonymous_usage(request: Request):
    """Increment usage counter for anonymous user"""
    client_id = get_client_identifier(request)
    current_month = datetime.now().strftime("%Y-%m")
    usage_key = f"usage:{client_id}:{current_month}"
    
    redis_client.incr(usage_key)
    # Expire after 32 days (to cover month boundaries)
    redis_client.expire(usage_key, int(timedelta(days=32).total_seconds()))

def reset_monthly_usage():
    """Reset monthly usage counters for all users (run monthly)"""
    # This would be called by a scheduled job
    pass 