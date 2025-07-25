from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.orm import Session
from app.cleaner import CSVCleaner
from app.auth import get_current_user_optional
from app.database import get_db
from app.models import User
from app.config import settings
import io
import time
import redis
from typing import Optional

# Import routes
try:
    from app.routes.auth import router as auth_router
except ImportError:
    # Fallback for development without auth features
    auth_router = None

app = FastAPI(
    title="CleanMyCSV.online API",
    description="AI-powered CSV cleaning service with anonymous usage and freemium model",
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Production middleware
if not settings.DEBUG:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
if auth_router:
    app.include_router(auth_router)

cleaner = CSVCleaner()

# Redis for anonymous usage tracking
redis_client = redis.from_url(settings.REDIS_URL)

def check_anonymous_usage(request: Request) -> dict:
    """Check anonymous usage for current session"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return {"used": 0, "remaining": settings.ANONYMOUS_FREE_LIMIT, "needs_signup": False}
    
    used = redis_client.get(f"anon_usage:{session_id}")
    used_count = int(used) if used else 0
    
    return {
        "used": used_count,
        "remaining": max(0, settings.ANONYMOUS_FREE_LIMIT - used_count),
        "needs_signup": used_count >= settings.ANONYMOUS_FREE_LIMIT
    }

def increment_anonymous_usage(request: Request):
    """Increment anonymous usage counter"""
    session_id = request.cookies.get("session_id")
    if session_id:
        redis_client.incr(f"anon_usage:{session_id}")

@app.post("/upload-csv")
async def upload_csv(
    request: Request,
    file: UploadFile,
    user_instructions: str = Form(""),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_optional(request, db)
    """Main CSV cleaning endpoint - works for anonymous and registered users"""
    
    start_time = time.time()
    
    # Check file type
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(400, "Only CSV files are supported")
    
    # Check file size
    file_size_mb = file.size / (1024 * 1024)
    
    if current_user:
        # Registered user - check their plan limits
        limits = settings.PLAN_LIMITS[current_user.plan]
        
        if file_size_mb > limits['max_file_size_mb']:
            raise HTTPException(400, f"File too large. Maximum size for {current_user.plan} plan is {limits['max_file_size_mb']}MB")
        
        if limits['files_per_month'] != -1 and current_user.files_processed_this_month >= limits['files_per_month']:
            raise HTTPException(400, f"Monthly limit reached. {current_user.plan} plan allows {limits['files_per_month']} files per month")
        
        basic_only = not limits['llm_features']
        
    else:
        # Anonymous user - check free usage
        if file_size_mb > settings.ANONYMOUS_FILE_SIZE_LIMIT_MB:
            raise HTTPException(400, f"File too large for anonymous usage. Maximum size is {settings.ANONYMOUS_FILE_SIZE_LIMIT_MB}MB")
        
        usage_info = check_anonymous_usage(request)
        if usage_info["needs_signup"]:
            raise HTTPException(400, "Free usage limit reached. Please sign up for more features.")
        
        basic_only = False  # Allow LLM features for anonymous users
    
    # Process CSV file with robust parsing
    try:
        # Read file content
        content = await file.read()
        
        # Try pandas first with error handling
        try:
            import pandas as pd
            df = pd.read_csv(io.BytesIO(content), on_bad_lines='skip', encoding='utf-8')
        except Exception as pandas_error:
            # Fallback to Python's csv module
            import csv
            import io as string_io
            
            try:
                content_str = content.decode('utf-8')
                csv_reader = csv.reader(string_io.StringIO(content_str))
                rows = list(csv_reader)
                
                if len(rows) < 2:
                    raise HTTPException(400, "CSV file must have at least a header and one data row")
                
                # Create DataFrame from parsed CSV
                import pandas as pd
                df = pd.DataFrame(rows[1:], columns=rows[0])
                
            except Exception as csv_error:
                raise HTTPException(400, f"Failed to parse CSV file: {str(csv_error)}")
        
        if df.empty:
            raise HTTPException(400, "CSV file is empty or could not be parsed")
        
        # Clean the data
        result = cleaner.clean_data(df, user_instructions, basic_only=basic_only)
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Update usage counters
        if current_user:
            current_user.files_processed_this_month += 1
            current_user.total_files_processed += 1
            db.commit()
        else:
            increment_anonymous_usage(request)
            # Add usage info to response
            usage_after = check_anonymous_usage(request)
            result["usage_info"] = {
                "remaining_free": usage_after["remaining"], 
                "show_signup_prompt": usage_after["remaining"] <= 1
            }
        
        # Convert cleaned DataFrame to CSV for download
        csv_buffer = io.StringIO()
        result['cleaned_data'].to_csv(csv_buffer, index=False)
        result['download_csv'] = csv_buffer.getvalue()
        
        # Remove DataFrame from response (not JSON serializable)
        del result['cleaned_data']
        
        return result
        
    except Exception as e:
        raise HTTPException(500, f"Processing failed: {str(e)}")

@app.get("/usage-info")
async def get_usage_info(
    request: Request, 
    db: Session = Depends(get_db)
):
    current_user = get_current_user_optional(request, db)
    """Get usage information for current user or anonymous session"""
    
    if current_user:
        # Registered user
        limits = settings.PLAN_LIMITS[current_user.plan]
        return {
            "plan": current_user.plan,
            "files_used": current_user.files_processed_this_month,
            "files_limit": limits['files_per_month'],
            "file_size_limit_mb": limits['max_file_size_mb'],
            "llm_features": limits['llm_features'],
            "is_email_verified": current_user.is_email_verified
        }
    else:
        # Anonymous user
        usage_info = check_anonymous_usage(request)
        return {
            "plan": "anonymous",
            "files_used": usage_info["used"],
            "files_limit": settings.ANONYMOUS_FREE_LIMIT,
            "file_size_limit_mb": settings.ANONYMOUS_FILE_SIZE_LIMIT_MB,
            "llm_features": True,
            "remaining_free": usage_info["remaining"],
            "needs_signup": usage_info["needs_signup"]
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CleanMyCSV.online API",
        "version": "2.0.0",
        "docs": "/docs" if settings.DEBUG else None
    } 