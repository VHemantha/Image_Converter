# Docker Setup Guide - Image Converter Pro

Complete Docker deployment with Flask, Redis, Celery Worker, and Celery Beat.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- 2GB+ free disk space
- Ports 5000 and 6379 available

### Start All Services

```bash
# Build and start all containers
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**That's it!** Your application is now running at http://localhost:5000

## 📦 What's Included

The Docker Compose setup includes **4 services**:

### 1. **Redis** (Message Broker)
- **Container**: `image_converter_redis`
- **Port**: 6379
- **Image**: `redis:7-alpine` (lightweight)
- **Purpose**: Message broker and result backend for Celery
- **Data**: Persisted in named volume `redis_data`

### 2. **Flask Web App**
- **Container**: `image_converter_web`
- **Port**: 5000
- **Purpose**: Web interface and API endpoints
- **Workers**: 4 Gunicorn workers with gevent
- **Health Check**: `/health` endpoint every 30s

### 3. **Celery Worker**
- **Container**: `image_converter_celery_worker`
- **Purpose**: Background image processing
- **Concurrency**: 4 workers
- **Queues**: `conversions` and `cleanup`

### 4. **Celery Beat**
- **Container**: `image_converter_celery_beat`
- **Purpose**: Periodic cleanup scheduler
- **Schedule**: Cleanup every 15 minutes

## 🔧 Docker Commands

### Start/Stop Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d web

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery_worker
docker-compose logs -f redis

# Last 100 lines
docker-compose logs --tail=100 web
```

### Check Status

```bash
# List running containers
docker-compose ps

# Check health status
docker-compose ps --filter health=healthy

# Inspect specific service
docker inspect image_converter_web
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart web
docker-compose restart celery_worker
```

### Execute Commands in Container

```bash
# Open bash shell in web container
docker-compose exec web bash

# Run Python shell
docker-compose exec web python

# Check Celery worker status
docker-compose exec celery_worker celery -A celery_worker.celery_app inspect active

# Check Redis
docker-compose exec redis redis-cli ping
```

## 🏗️ Building and Deploying

### Build from Scratch

```bash
# Build all images
docker-compose build

# Build without cache (fresh build)
docker-compose build --no-cache

# Build specific service
docker-compose build web
```

### Update After Code Changes

```bash
# Rebuild and restart
docker-compose up -d --build

# Force recreate containers
docker-compose up -d --force-recreate
```

### Production Deployment

```bash
# Set production environment
export FLASK_ENV=production
export SECRET_KEY=your-super-secret-key-here

# Start with production config
docker-compose up -d

# Scale Celery workers
docker-compose up -d --scale celery_worker=8
```

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=change-this-to-a-random-secret-key

# Redis Configuration (default: redis://redis:6379)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# File Upload Limits
MAX_CONTENT_LENGTH=52428800  # 50MB
FILE_RETENTION_MINUTES=60

# Paths (inside container)
UPLOAD_FOLDER=/app/temp/uploads
CONVERTED_FOLDER=/app/temp/converted

# Security
ALLOWED_EXTENSIONS=jpg,jpeg,png,webp,avif,tiff,bmp,gif,ico,heic
```

## 📊 Monitoring

### Health Checks

All services have health checks:

```bash
# Web app health
curl http://localhost:5000/health

# Redis health
docker-compose exec redis redis-cli ping

# Celery worker health
docker-compose exec celery_worker celery -A celery_worker.celery_app inspect ping
```

### Resource Usage

```bash
# View resource consumption
docker stats

# Specific container
docker stats image_converter_web
```

### Service Logs Analysis

```bash
# Count errors in logs
docker-compose logs web | grep ERROR | wc -l

# Find specific errors
docker-compose logs web | grep "Traceback"

# Monitor live errors
docker-compose logs -f web | grep ERROR
```

## 🔄 Data Persistence

### Volumes

- **redis_data**: Redis database persistence
- **./temp**: Temporary upload/converted files (bind mount)
- **./logs**: Application logs (bind mount)

### Backup Redis Data

```bash
# Create backup
docker-compose exec redis redis-cli SAVE
docker cp image_converter_redis:/data/dump.rdb ./backup_$(date +%Y%m%d).rdb

# Restore backup
docker cp ./backup_20260214.rdb image_converter_redis:/data/dump.rdb
docker-compose restart redis
```

### Clean Temporary Files

```bash
# From host
rm -rf temp/uploads/*
rm -rf temp/converted/*

# From container
docker-compose exec web rm -rf /app/temp/uploads/*
docker-compose exec web rm -rf /app/temp/converted/*
```

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker-compose logs web

# Check if ports are available
netstat -an | grep :5000
netstat -an | grep :6379

# Remove and recreate
docker-compose down
docker-compose up -d
```

### Celery Worker Not Processing

```bash
# Check worker is registered
docker-compose exec celery_worker celery -A celery_worker.celery_app inspect active

# Check Redis connection
docker-compose exec celery_worker celery -A celery_worker.celery_app inspect ping

# View worker logs
docker-compose logs -f celery_worker
```

### Redis Connection Failed

```bash
# Test Redis
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

### Web App Returns 502

```bash
# Check if Gunicorn is running
docker-compose exec web ps aux | grep gunicorn

# Check health endpoint
curl http://localhost:5000/health

# Restart web service
docker-compose restart web
```

### "Out of Memory" Errors

```bash
# Check memory usage
docker stats

# Increase Docker Desktop memory (Settings > Resources)
# Or reduce worker count
docker-compose up -d --scale celery_worker=2
```

## 🔧 Advanced Configuration

### Custom Network

```yaml
# In docker-compose.yml
networks:
  image_converter_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

### Resource Limits

```yaml
# Add to service in docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

### Using External Redis

```yaml
# In docker-compose.yml, comment out redis service
# Update environment variables:
environment:
  - CELERY_BROKER_URL=redis://external-redis:6379/0
  - CELERY_RESULT_BACKEND=redis://external-redis:6379/1
```

## 📈 Performance Tuning

### Scale Workers

```bash
# 8 Celery workers
docker-compose up -d --scale celery_worker=8

# 8 Gunicorn workers in web container
# Edit docker-compose.yml:
command: gunicorn --bind 0.0.0.0:5000 --workers 8 --worker-class gevent run:app
```

### Optimize Redis

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Set max memory (inside redis-cli)
CONFIG SET maxmemory 512mb
CONFIG SET maxmemory-policy allkeys-lru

# Save config
CONFIG REWRITE
```

## 🚀 Production Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` in environment variables
- [ ] Set `FLASK_ENV=production`
- [ ] Configure proper resource limits
- [ ] Set up log rotation
- [ ] Configure backup for Redis data
- [ ] Add Nginx reverse proxy (optional)
- [ ] Enable HTTPS/SSL certificates
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure firewall rules
- [ ] Test disaster recovery

## 📚 Additional Resources

- **Dockerfile**: [Dockerfile](Dockerfile)
- **Compose File**: [docker-compose.yml](docker-compose.yml)
- **Ignore File**: [.dockerignore](.dockerignore)
- **Worker Entry**: [celery_worker.py](celery_worker.py)

## 🎯 Next Steps

1. **Start services**: `docker-compose up -d`
2. **Test app**: http://localhost:5000
3. **Monitor logs**: `docker-compose logs -f`
4. **Upload images**: Test conversion functionality
5. **Check health**: `curl http://localhost:5000/health`

---

**Current Setup**: Development mode with Docker Compose
**For Production**: Add Nginx reverse proxy and SSL (Phase 5)
**Documentation**: See [README.md](README.md) for full project documentation
