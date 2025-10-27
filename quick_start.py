#!/usr/bin/env python3
"""
StudyMate AI - Quick Start Script
Simple startup without complex checks
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

def main():
    print("🧠 Starting StudyMate AI...")
    
    # Create basic directories
    for directory in ["uploads", "static", "logs"]:
        Path(directory).mkdir(exist_ok=True)
    
    # Start server
    try:
        import uvicorn
        print("🚀 Server starting on http://localhost:8080")
        print("🎓 StudyMate AI Dark Edition Ready!")
        print("🛑 Press Ctrl+C to stop")
        
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8080,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 StudyMate AI stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Try: pip install uvicorn fastapi")

if __name__ == "__main__":
    main()