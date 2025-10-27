# 🚀 StudyMate AI - Deployment Guide

## 📋 Pre-Deployment Checklist

### ✅ System Requirements
- **Python**: 3.8 or higher
- **RAM**: Minimum 4GB (8GB+ recommended for large documents)
- **Storage**: 2GB free space for dependencies and data
- **Internet**: Required for AI API calls (Gemini, ElevenLabs)

### ✅ API Keys Required
1. **Gemini AI API Key** (Required)
   - Get from: https://makersuite.google.com/app/apikey
   - Free tier: 60 requests per minute
   
2. **ElevenLabs API Key** (Optional)
   - Get from: https://elevenlabs.io
   - For premium voice synthesis
   - Falls back to browser TTS if not provided

## 🚀 Quick Deployment

### Option 1: Automated Setup (Recommended)

**Windows:**
```cmd
# Double-click or run in Command Prompt
start_studymate.bat
```

**Linux/Mac:**
```bash
# Make executable and run
chmod +x start_studymate.sh
./start_studymate.sh
```

**Cross-Platform:**
```bash
python start_studymate.py
```

### Option 2: Manual Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   ```bash
   # Copy template
   cp .env.example .env
   
   # Edit .env file with your API keys
   GEMINI_API_KEY=your_gemini_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ```

3. **Start Application:**
   ```bash
   python run_studymate.py
   ```

## 🌐 Access Points

Once deployed, access StudyMate at:

- **Main Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc

## 🔧 Configuration Options

### Environment Variables (.env)

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
DEBUG=False
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///./studymate.db
SECRET_KEY=change-this-in-production

# File Upload Settings
MAX_FILE_SIZE_MB=50
UPLOAD_DIR=uploads

# RAG Settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

### Port Configuration

To change the default port (8000):

1. **Environment Variable:**
   ```env
   PORT=3000
   ```

2. **Command Line:**
   ```bash
   python run_studymate.py --port 3000
   ```

## 🐳 Docker Deployment (Advanced)

### Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run_studymate.py"]
```

### Build and Run
```bash
# Build image
docker build -t studymate-ai .

# Run container
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key studymate-ai
```

## ☁️ Cloud Deployment

### Heroku
```bash
# Install Heroku CLI
# Create Procfile
echo "web: python run_studymate.py --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku create your-studymate-app
heroku config:set GEMINI_API_KEY=your_key
git push heroku main
```

### Railway
```bash
# Install Railway CLI
railway login
railway init
railway add
railway deploy
```

### DigitalOcean App Platform
1. Connect your GitHub repository
2. Set environment variables in the dashboard
3. Deploy with one click

## 🔒 Security Considerations

### Production Deployment
1. **Change Secret Key:**
   ```env
   SECRET_KEY=your-secure-random-secret-key
   ```

2. **Disable Debug Mode:**
   ```env
   DEBUG=False
   ```

3. **Use HTTPS:**
   - Configure reverse proxy (nginx/Apache)
   - Use SSL certificates (Let's Encrypt)

4. **Environment Variables:**
   - Never commit `.env` to version control
   - Use secure environment variable management

### File Upload Security
- Files are processed locally
- Automatic virus scanning (if antivirus available)
- Size limits enforced (50MB default)
- Type validation (PDF, DOCX, PPTX, TXT only)

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# Check if service is running
curl http://localhost:8000/health

# API status
curl http://localhost:8000/api/status
```

### Log Files
- Application logs: `logs/studymate.log`
- Error logs: `logs/error.log`
- Access logs: `logs/access.log`

### Database Maintenance
```bash
# Backup database
cp studymate.db studymate_backup_$(date +%Y%m%d).db

# Clean old sessions (optional)
python -c "from database.db_manager import cleanup_old_sessions; cleanup_old_sessions()"
```

## 🚨 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Find process using port 8000
netstat -tulpn | grep :8000

# Kill process (Linux/Mac)
kill -9 <PID>

# Kill process (Windows)
taskkill /PID <PID> /F
```

**Permission Errors:**
```bash
# Linux/Mac: Fix permissions
chmod 755 start_studymate.sh
sudo chown -R $USER:$USER StudyMate/

# Windows: Run as Administrator
```

**Memory Issues:**
- Reduce document size
- Increase system RAM
- Use smaller embedding model:
  ```env
  EMBEDDING_MODEL=all-MiniLM-L12-v2
  ```

**API Key Errors:**
- Verify keys in `.env` file
- Check API quotas and limits
- Test keys independently

### Performance Optimization

1. **Use SSD Storage** for faster file processing
2. **Increase RAM** for larger document processing
3. **Use GPU** for faster embeddings (optional)
4. **Enable Caching** for repeated queries

## 📈 Scaling

### Horizontal Scaling
- Use load balancer (nginx, HAProxy)
- Deploy multiple instances
- Shared database (PostgreSQL, MySQL)

### Vertical Scaling
- Increase server resources
- Optimize database queries
- Use Redis for caching

## 🔄 Updates & Maintenance

### Updating StudyMate
```bash
# Backup current installation
cp -r StudyMate StudyMate_backup

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart application
python run_studymate.py
```

### Database Migrations
```bash
# Run migrations (if any)
python -c "from database.db_manager import run_migrations; run_migrations()"
```

## 📞 Support

### Getting Help
1. **Documentation**: Check README.md and API docs
2. **Logs**: Review application logs for errors
3. **Community**: GitHub Issues and Discussions
4. **Debug Mode**: Enable for detailed error messages

### Reporting Issues
Include in your report:
- Operating system and version
- Python version
- Error messages and logs
- Steps to reproduce
- Configuration (without API keys)

---

**🎓 StudyMate AI is now ready for deployment!**

*For additional support, visit our GitHub repository or documentation.*