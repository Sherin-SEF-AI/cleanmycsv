#!/usr/bin/env python3
"""
Production setup script for CleanMyCSV.online
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def setup_database():
    """Setup database tables"""
    print("\n📊 Setting up database...")
    
    # Import and create tables
    try:
        from app.database import create_tables
        create_tables()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False
    
    return True

def setup_environment():
    """Setup environment variables"""
    print("\n🔧 Setting up environment...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found. Please create it from env.example")
        return False
    
    print("✅ Environment file found")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")
    
    if run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return True
    return False

def setup_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "logs",
        "uploads",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True

def setup_ssl():
    """Setup SSL certificates (for production)"""
    print("\n🔒 SSL setup...")
    
    # Check if running in production
    if os.getenv("ENVIRONMENT") == "production":
        print("⚠️  Production environment detected. Please ensure SSL certificates are configured.")
        print("   Consider using Let's Encrypt or your hosting provider's SSL service.")
    else:
        print("✅ Development environment - SSL not required")
    
    return True

def main():
    """Main setup function"""
    print("🚀 CleanMyCSV.online Production Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Setup steps
    steps = [
        ("Environment", setup_environment),
        ("Dependencies", install_dependencies),
        ("Directories", setup_directories),
        ("Database", setup_database),
        ("SSL", setup_ssl)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        if not step_func():
            failed_steps.append(step_name)
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Setup Summary")
    print("=" * 50)
    
    if failed_steps:
        print(f"❌ Failed steps: {', '.join(failed_steps)}")
        print("\n🔧 Manual steps required:")
        print("1. Configure your .env file with proper values")
        print("2. Set up Razorpay account and get API keys")
        print("3. Configure email settings for verification emails")
        print("4. Set up SSL certificates for production")
        print("5. Configure your web server (nginx/apache)")
        return False
    else:
        print("✅ All setup steps completed successfully!")
        print("\n🎉 CleanMyCSV.online is ready for production!")
        print("\n📝 Next steps:")
        print("1. Configure your web server")
        print("2. Set up SSL certificates")
        print("3. Configure monitoring and logging")
        print("4. Test all functionality")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 