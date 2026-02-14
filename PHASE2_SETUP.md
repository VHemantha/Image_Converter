# Phase 2: Asynchronous Processing Setup Guide

## Overview

Phase 2 adds asynchronous image processing using Celery and Redis. Your application now has **smart fallback** - it works synchronously without Redis, but enables async processing when Redis is available.

## Current Status

✅ **Phase 2 Code**: Fully implemented and integrated
✅ **Fallback Mode**: App works synchronously without Redis
⚠️ **Redis**: Not yet running (required for async processing)
⚠️ **Celery Worker**: Not yet started (required for async processing)

## What's New in Phase 2

### New Features
- **Asynchronous Processing**: Convert images in background without blocking
- **Progress Tracking**: Real-time status updates via `/status/<task_id>` endpoint
- **Batch Processing**: Handle multiple files efficiently
- **Automatic Cleanup**: Periodic cleanup of old files every 15 minutes
- **Task Queues**: Separate queues for conversions and cleanup tasks

### New Files Added
```
app/tasks/
├── celery_config.py      # Celery configuration (Redis URLs, task limits)
├── celery_app.py         # Celery instance
├── conversion_tasks.py   # Async conversion tasks
└── cleanup_tasks.py      # Periodic cleanup tasks
```

## Setup Options

### Option 1: Docker (Recommended)

**Prerequisites**: Docker Desktop must be running

```bash
# Start Docker Desktop first, then:
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Verify Redis is running:
docker ps
```

### Option 2: Redis for Windows

Download and install Redis for Windows:
1. Visit https://github.com/microsoftarchive/redis/releases
2. Download **Redis-x64-3.2.100.msi**
3. Install with default settings
4. Redis will run as a Windows service automatically

### Option 3: WSL + Redis

If you have WSL installed:
```bash
# In WSL terminal:
sudo apt-get update
sudo apt-get install redis-server
sudo service redis-server start

# Verify:
redis-cli ping
# Should return: PONG
```

### Option 4: Continue Without Redis

The app works perfectly in synchronous mode! No setup needed - conversions happen immediately without background workers.

## Starting Celery Workers

Once Redis is running, start Celery workers to enable async processing:

### Terminal 1: Start Flask App
```bash
cd c:\Users\Viraj\Documents\Image_Converter\Image_Converter
python run.py
```

### Terminal 2: Start Celery Worker
```bash
cd c:\Users\Viraj\Documents\Image_Converter\Image_Converter
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

**Note**: The `--pool=solo` flag is required on Windows.

### Terminal 3: Start Celery Beat (Optional - For Periodic Cleanup)
```bash
cd c:\Users\Viraj\Documents\Image_Converter\Image_Converter
celery -A app.tasks.celery_app beat --loglevel=info
```

## Testing Async Processing

### 1. Check Redis Connection
```bash
# If using Docker:
docker exec -it redis redis-cli ping
# Should return: PONG

# If using Redis for Windows or WSL:
redis-cli ping
# Should return: PONG
```

### 2. Test Conversion Flow

**Upload images** via the web interface at http://localhost:5000

**With Redis running**, the response will include:
```json
{
  "success": true,
  "task_id": "abc123...",
  "status": "processing",
  "async": true,
  "total_files": 2
}
```

**Without Redis** (fallback mode), the response will include:
```json
{
  "success": true,
  "task_id": "abc123...",
  "results": [...],
  "async": false,
  "total_files": 2
}
```

### 3. Check Task Progress

```bash
# In browser or using curl:
curl http://localhost:5000/status/<task_id>
```

Response:
```json
{
  "state": "PROGRESS",
  "current": 1,
  "total": 2,
  "progress": 50,
  "status": "Converting file 1 of 2: example.jpg"
}
```

## Configuration

All Redis settings are in [.env](.env):

```env
# Celery/Redis Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

To use a different Redis host/port:
```env
CELERY_BROKER_URL=redis://your-redis-host:6379/0
CELERY_RESULT_BACKEND=redis://your-redis-host:6379/1
```

## Task Configuration

### Conversion Tasks
- **Queue**: `conversions`
- **Time Limit**: 5 minutes (300 seconds)
- **Soft Time Limit**: 4.5 minutes (270 seconds)
- **Progress Updates**: Real-time via task state

### Cleanup Tasks
- **Queue**: `cleanup`
- **Schedule**: Every 15 minutes
- **Retention**: Files older than configured `FILE_RETENTION_MINUTES` (default: 60 minutes)

### Worker Settings
- **Prefetch Multiplier**: 1 (process one task at a time)
- **Acknowledgment**: Late (after task completion)
- **Task Recovery**: Requeue if worker dies

## Monitoring

### Check Celery Worker Health
```bash
celery -A app.tasks.celery_app inspect active
celery -A app.tasks.celery_app inspect stats
```

### Check Redis Stats
```bash
redis-cli info stats
```

### View Task Results in Redis
```bash
redis-cli
> KEYS *
> GET celery-task-meta-<task_id>
```

## Troubleshooting

### "No module named 'celery'"
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### "Error 111 connecting to localhost:6379. Connection refused"
**Solution**: Redis is not running. Start Redis using one of the options above.

### "Error during connect: ... dockerDesktopLinuxEngine"
**Solution**: Start Docker Desktop, then retry the redis container command.

### Tasks stuck in PENDING state
**Possible causes**:
1. Celery worker not running
2. Redis connection issue
3. Wrong broker URL in .env

**Solution**:
- Check Celery worker is running: `celery -A app.tasks.celery_app inspect active`
- Verify Redis connection: `redis-cli ping`
- Check `.env` has correct `CELERY_BROKER_URL`

### "NotImplementedError: Windows does not support exec, use pool=solo"
**Solution**: Add `--pool=solo` flag when starting Celery worker on Windows
```bash
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

## Performance Tips

### For Development
- Use `--pool=solo` on Windows (simpler, easier debugging)
- Use `--loglevel=debug` for detailed logs
- Enable Flask debug mode (already set in .env)

### For Production (Future Phases)
- Use `--pool=gevent` or `--pool=eventlet` for better concurrency
- Set `--loglevel=info` or `--loglevel=warning`
- Use Gunicorn instead of Flask development server
- Deploy with Docker Compose (all services together)

## Next Steps

Once Redis and Celery are running:

1. ✅ **Test Async Conversions**: Upload images and verify tasks process in background
2. ✅ **Monitor Progress**: Check `/status/<task_id>` endpoint
3. ✅ **Test Cleanup**: Verify old files are removed automatically
4. 🔄 **Phase 3**: Real-time progress UI with Server-Sent Events (SSE)
5. 🔄 **Phase 4**: Production deployment with Docker Compose

## Quick Start Checklist

For the fastest path to async processing:

- [ ] Start Docker Desktop
- [ ] Run `docker run -d -p 6379:6379 --name redis redis:7-alpine`
- [ ] Open Terminal 1: `python run.py`
- [ ] Open Terminal 2: `celery -A app.tasks.celery_app worker --loglevel=info --pool=solo`
- [ ] Test upload at http://localhost:5000
- [ ] Check task status: http://localhost:5000/status/<task_id>

---

**Current Mode**: Synchronous Fallback (Phase 1)
**To Enable Async**: Follow Option 1, 2, or 3 above and start Celery worker
**Documentation**: See [README.md](README.md) for full project documentation
