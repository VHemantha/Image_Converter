# Image Converter - Quick Start Guide

## 🐳 Easiest: Docker (Recommended)

**One command to start everything!**

```bash
# Build and start all services (Flask, Redis, Celery)
docker-compose up -d

# Open browser
http://localhost:5000
```

**Includes**: Flask web app, Redis, Celery worker, Celery beat, automatic health checks!

[📚 Full Docker Guide →](DOCKER_SETUP.md)

---

## 🚀 Quick Start (No Docker - Synchronous Mode)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the app
python run.py

# 3. Open browser
http://localhost:5000
```

**That's it!** Upload images and convert between 9+ formats immediately.

---

## ⚡ Full Async Mode (No Docker - Manual Setup)

### Terminal 1: Start Redis
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

### Terminal 2: Start Flask
```bash
python run.py
```

### Terminal 3: Start Celery Worker
```bash
celery -A celery_worker.celery_app worker --loglevel=info --pool=solo
```

### Terminal 4: Start Celery Beat (Optional - Auto-cleanup)
```bash
celery -A celery_worker.celery_app beat --loglevel=info
```

### Test
```bash
# Run test suite
python test_async.py

# Or use the web UI
http://localhost:5000
```

---

## 📋 Configuration

Edit [.env](.env) to customize:

```env
# Flask
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# File Storage
UPLOAD_FOLDER=temp/uploads
CONVERTED_FOLDER=temp/converted
FILE_RETENTION_MINUTES=60

# Redis (for async processing)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Security
MAX_CONTENT_LENGTH=52428800  # 50MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,webp,avif,tiff,bmp,gif,ico,heic
```

---

## 🎯 Supported Formats

**All bidirectional conversions supported:**

- **JPG/JPEG** - Lossy, best for photos
- **PNG** - Lossless, best for graphics/screenshots
- **WebP** - Modern format, 30% smaller than JPEG
- **AVIF** - Next-gen format, best compression
- **TIFF** - Professional/archival, lossless
- **BMP** - Uncompressed, largest file size
- **GIF** - Supports animation, limited colors
- **ICO** - Icons for websites/apps
- **HEIC** - Apple's format (iPhone photos)

---

## 🛠️ Common Commands

### Check System Health
```bash
curl http://localhost:5000/health
curl http://localhost:5000/ready
```

### Check Task Status
```bash
curl http://localhost:5000/status/<task_id>
```

### Stop Redis Container
```bash
docker stop redis
docker rm redis
```

### View Celery Worker Stats
```bash
celery -A app.tasks.celery_app inspect active
celery -A app.tasks.celery_app inspect stats
```

### Check Redis Stats
```bash
docker exec -it redis redis-cli info stats
```

---

## 🔍 Troubleshooting

### App won't start
```bash
# Check if port 5000 is already in use
netstat -ano | findstr :5000

# Install missing dependencies
pip install -r requirements.txt
```

### Redis connection error
```bash
# Verify Docker Desktop is running
docker ps

# Start Redis container
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Test Redis connection
docker exec -it redis redis-cli ping
```

### Celery worker issues (Windows)
```bash
# Always use --pool=solo on Windows
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

### Tasks stuck in PENDING
- Ensure Celery worker is running
- Check Redis is accessible: `redis-cli ping`
- Verify `.env` has correct Redis URLs

---

## 📊 Features

### Current Implementation (Phase 1, 2 & 3)
- ✅ Quality preservation (95+ for lossy, lossless where possible)
- ✅ Async processing with Celery
- ✅ **Real-time progress with SSE** (Phase 3)
- ✅ **Animated progress bars** (Phase 3)
- ✅ **ZIP download for batch conversions** (Phase 3)
- ✅ Automatic file cleanup
- ✅ Rate limiting (30 req/min)
- ✅ CSRF protection
- ✅ File validation (magic numbers)
- ✅ Docker Compose deployment

### Upcoming (Phase 4+)
- 🔄 Nginx reverse proxy
- 🔄 SSL/HTTPS certificates
- 🔄 Production monitoring
- 🔄 Advanced image editing
- 🔄 User accounts and history

---

## 📂 Project Structure

```
Image_Converter/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── routes.py                # Routes (main, upload, download, status)
│   ├── config.py                # Configuration classes
│   ├── forms.py                 # Flask-WTF forms
│   ├── static/                  # CSS, JS, images
│   ├── templates/               # HTML templates
│   ├── utils/                   # File validator, image converter
│   └── tasks/                   # Celery tasks (Phase 2)
│       ├── celery_config.py     # Celery configuration
│       ├── celery_app.py        # Celery instance
│       ├── conversion_tasks.py  # Async conversion tasks
│       └── cleanup_tasks.py     # Periodic cleanup
├── temp/                        # Temporary files (auto-created)
│   ├── uploads/                 # Uploaded files
│   └── converted/               # Converted files
├── .env                         # Environment variables
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
├── QUICKSTART.md               # This file
├── PHASE2_SETUP.md             # Detailed Phase 2 guide
└── test_async.py               # Async processing test suite
```

---

## 🎓 Learn More

- **Detailed Setup**: [PHASE2_SETUP.md](PHASE2_SETUP.md)
- **Full Documentation**: [README.md](README.md)
- **Test Suite**: Run `python test_async.py`

---

## ⚡ Quick Reference

| Action | Command |
|--------|---------|
| Start with Docker | `docker-compose up -d` |
| Start app (sync) | `python run.py` |
| Start Redis | `docker run -d -p 6379:6379 --name redis redis:7-alpine` |
| Start Celery worker | `celery -A celery_worker.celery_app worker --pool=solo --loglevel=info` |
| Start Celery beat | `celery -A celery_worker.celery_app beat --loglevel=info` |
| Docker logs | `docker-compose logs -f` |
| Stop Docker | `docker-compose down` |
| Run tests | `python test_async.py` |
| Check health | `curl http://localhost:5000/health` |
| View formats | `curl http://localhost:5000/formats` |
| Stop Redis | `docker stop redis && docker rm redis` |

---

**Current Phase**: Phase 2 (Async Processing) ✅ Complete
**Mode**: Smart Fallback (works with or without Redis)
**Web UI**: http://localhost:5000

For production deployment, see Phase 4 in the implementation plan.
