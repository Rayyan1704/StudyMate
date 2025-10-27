#!/usr/bin/env python3
"""
StudyMate AI - Startup Script
Handles environment setup and launches the application
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import google.generativeai
        print("✅ Core dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found")
        create_env_file()
        return False
    
    # Check for required variables
    with open(env_path, 'r') as f:
        content = f.read()
        
    required_vars = ['GEMINI_API_KEY', 'ELEVENLABS_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if f"{var}=" not in content or f"{var}=your_" in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or incomplete environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with valid API keys")
        return False
    
    print("✅ Environment configuration found")
    return True

def create_env_file():
    """Create a template .env file"""
    env_template = """# StudyMate AI - Environment Configuration

# Required: Gemini AI API Key (Get from: https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: ElevenLabs API Key for premium voice (Get from: https://elevenlabs.io)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Application Settings
DEBUG=False
HOST=127.0.0.1
PORT=8000

# Database
DATABASE_URL=sqlite:///./studymate.db

# Security
SECRET_KEY=your-secret-key-change-this-in-production
"""
    
    with open(".env", "w") as f:
        f.write(env_template)
    
    print("📝 Created .env template file")
    print("Please edit .env and add your API keys before running StudyMate")

def create_directories():
    """Create necessary directories"""
    directories = [
        "uploads",
        "database",
        "logs",
        "static/icons"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created necessary directories")

def launch_studymate():
    """Launch the StudyMate application"""
    print("🚀 Starting StudyMate AI...")
    print("📱 Web Interface: http://127.0.0.1:8000")
    print("📚 API Documentation: http://127.0.0.1:8000/docs")
    print("🛑 Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        # Import and run the application
        from main import app
        import uvicorn
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 StudyMate AI stopped")
    except Exception as e:
        print(f"❌ Error starting StudyMate: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    print("🎓 StudyMate AI - Startup")
    print("=" * 30)
    
    # Check Python version
    check_python_version()
    
    # Create necessary directories
    create_directories()
    
    # Check dependencies
    if not check_dependencies():
        print("Installing missing dependencies...")
        if not install_dependencies():
            print("❌ Failed to install dependencies. Please install manually:")
            print("pip install -r requirements.txt")
            sys.exit(1)
    
    # Check environment configuration
    if not check_env_file():
        print("\n⚠️  Please configure your .env file and run again")
        sys.exit(1)
    
    # Launch the application
    launch_studymate()

if __name__ == "__main__":
    main()