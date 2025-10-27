# 🚀 StudyMate AI - Installation Guide

## Prerequisites

- **Python 3.8+** (Python 3.9+ recommended)
- **Git** (for cloning the repository)
- **Modern web browser** (Chrome, Firefox, Safari, Edge)
- **Internet connection** (for AI API calls)

## Step-by-Step Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd StudyMate
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv studymate_env

# Activate virtual environment
# Windows:
studymate_env\Scripts\activate
# Linux/Mac:
source studymate_env/bin/activate
```

### 3. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Alternative: Install core dependencies only
pip install -r requirements-core.txt
```

### 4. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys
# Minimum required: GEMINI_API_KEY
```

**Get your Gemini API Key:**
1. Visit https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Create a new API key
4. Copy the key to your `.env` file

### 5. Run StudyMate

**Option 1: Quick Start (Easiest)**
```bash
python quick_start.py
```

**Option 2: Direct Run**
```bash
python main.py
```

**Option 3: Using Scripts**
```bash
# Windows
start_studymate.bat

# Linux/Mac
chmod +x start_studymate.sh
./start_studymate.sh

# Cross-platform Python script
python start_studymate.py
```

### 6. Access StudyMate

Open your web browser and go to:
```
http://localhost:8080
```

## Verification

After installation, you should see:
1. ✅ StudyMate AI welcome screen
2. ✅ Clean dark interface
3. ✅ Ability to create new sessions
4. ✅ File upload functionality
5. ✅ AI responses working

## Troubleshooting

### Common Installation Issues

**1. Python Version Error**
```bash
# Check Python version
python --version
# Should be 3.8 or higher
```

**2. Pip Installation Fails**
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Try installing with --no-cache-dir
pip install --no-cache-dir -r requirements.txt
```

**3. Virtual Environment Issues**
```bash
# Deactivate and recreate
deactivate
rm -rf studymate_env
python -m venv studymate_env
```

**4. Port Already in Use**
```bash
# Change port in .env file
PORT=8081
```

**5. API Key Issues**
- Ensure GEMINI_API_KEY is correctly set in .env
- Check for extra spaces or quotes around the key
- Verify the key is valid at https://makersuite.google.com/

### System-Specific Notes

**Windows:**
- Use `python` command (not `python3`)
- Ensure Python is in your PATH
- May need to install Visual C++ Build Tools for some packages

**Linux/Ubuntu:**
```bash
# Install system dependencies
sudo apt update
sudo apt install python3-pip python3-venv python3-dev
```

**macOS:**
```bash
# Install using Homebrew
brew install python
# or use system Python with pip
```

## Optional Features Setup

### Voice Features (ElevenLabs)
1. Get API key from https://elevenlabs.io/
2. Add to .env: `ELEVENLABS_API_KEY=your_key_here`
3. Restart StudyMate

### Development Mode
```bash
# Set in .env file
DEBUG=True
```

## Performance Optimization

### For Better Performance:
1. **Use SSD storage** for faster file processing
2. **Allocate sufficient RAM** (minimum 4GB recommended)
3. **Close unnecessary browser tabs** during heavy document processing
4. **Use wired internet connection** for faster AI responses

### Resource Usage:
- **RAM**: 1-2GB during normal operation
- **Storage**: 500MB base + uploaded documents
- **CPU**: Moderate during document processing
- **Network**: Only for AI API calls

## Security Considerations

1. **Keep API keys secure** - never commit .env to version control
2. **Use HTTPS in production** - configure reverse proxy if needed
3. **Regular updates** - keep dependencies updated
4. **Firewall rules** - restrict access if running on server

## Next Steps

After successful installation:
1. 📖 Read the `USER_GUIDE.txt` for detailed usage instructions
2. 🎯 Create your first study session
3. 📚 Upload some documents to test functionality
4. 🎨 Customize the interface to your liking
5. 🗣️ Try voice features if configured

## Getting Help

If you encounter issues:
1. Check this installation guide
2. Review the troubleshooting section
3. Check the GitHub issues page
4. Create a new issue with detailed error information

---

**Happy Learning! 🎓✨**