"""
StudyMate AI - Startup Script
Run this to start the StudyMate AI application
"""

import os
import sys
import asyncio
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

def check_requirements():
    """Check if all required packages are installed"""
    # Core required packages
    core_packages = [
        ('fastapi', 'FastAPI web framework'),
        ('uvicorn', 'ASGI server'),
        ('google.generativeai', 'Gemini AI'),
        ('sentence_transformers', 'Text embeddings'),
        ('fitz', 'PDF processing (PyMuPDF)'),
        ('pptx', 'PowerPoint processing'),
        ('docx', 'Word document processing'),
    ]
    
    # Optional packages
    optional_packages = [
        ('faiss', 'Vector search (better RAG performance)'),
        ('whisper', 'Speech recognition'),
        ('elevenlabs', 'Text-to-speech'),
        ('chromadb', 'Vector database'),
    ]
    
    missing_core = []
    for package, description in core_packages:
        try:
            if '.' in package:
                # Handle packages with dots like google.generativeai
                import importlib
                importlib.import_module(package)
            else:
                __import__(package.replace('-', '_'))
        except ImportError:
            missing_core.append((package, description))
    
    if missing_core:
        print("❌ Missing core packages:")
        for package, desc in missing_core:
            print(f"   - {package} ({desc})")
        print("\n💡 Install core packages with:")
        print("   pip install -r requirements-core.txt")
        return False
    
    print("✅ All core packages available")
    
    # Check optional packages
    missing_optional = []
    for package, description in optional_packages:
        try:
            __import__(package.replace('-', '_').replace('.', '_'))
        except ImportError:
            missing_optional.append((package, description))
    
    if missing_optional:
        print("\n⚠️  Optional packages not installed (advanced features disabled):")
        for package, desc in missing_optional:
            print(f"   - {package} ({desc})")
        print("\n💡 Install optional packages with:")
        print("   pip install -r requirements-optional.txt")
    else:
        print("✅ All optional packages available")
    
    return True

def check_environment():
    """Check environment configuration"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  No .env file found. Creating from example...")
        example_env = Path(".env.example")
        if example_env.exists():
            import shutil
            shutil.copy(example_env, env_file)
            print("✅ Created .env file from example")
            print("🔧 Please edit .env file and add your API keys")
        else:
            print("❌ No .env.example file found")
            return False
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded from .env file")
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment")
    
    # Check critical environment variables
    gemini_key = os.getenv("GEMINI_API_KEY")
    print(f"🔍 Found Gemini API key: {gemini_key[:10]}..." if gemini_key else "🔍 No Gemini API key found")
    
    if not gemini_key or gemini_key == "your_gemini_api_key_here":
        print("⚠️  GEMINI_API_KEY not configured in .env file")
        print("   Get your API key from: https://makersuite.google.com/app/apikey")
        print("   📝 Edit the .env file and replace 'your_gemini_api_key_here' with your actual API key")
        print("\n🚀 Starting in demo mode (limited functionality)...")
        return True  # Allow demo mode
    else:
        print("✅ Gemini API key configured successfully!")
    
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        "uploads", "static", "static/audio", "rag_storage", 
        "temp", "logs", "backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Created necessary directories")

async def initialize_app():
    """Initialize the application"""
    try:
        from database.db_manager import DatabaseManager
        
        # Initialize database
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        print("✅ Application initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing application: {e}")
        return False

def main():
    """Main startup function"""
    print("🎓 Starting StudyMate AI...")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        print("\n💡 Please configure your .env file and restart")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Initialize app
    if not asyncio.run(initialize_app()):
        sys.exit(1)
    
    # Start the server
    print("\n🚀 Starting StudyMate AI server...")
    print("📱 Web interface: http://localhost:8000")
    print("📚 API docs: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", 8000)),
            reload=os.getenv("DEBUG", "True").lower() == "true"
        )
    except KeyboardInterrupt:
        print("\n👋 StudyMate AI stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()