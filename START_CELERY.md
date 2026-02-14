# How to Start Celery Worker (UPDATED)

## ⚠️ IMPORTANT: Use the New Command

The Celery worker needs to be started with the `celery_worker` module to ensure proper Flask app context.

## Start Celery Worker

**Stop the old worker if running** (Ctrl+C in the terminal)

**Start with the new command:**

```bash
cd c:\Users\Viraj\Documents\Image_Converter\Image_Converter
celery -A celery_worker.celery_app worker --loglevel=info --pool=solo
```

## What Changed?

**Old command** (had import issues):
```bash
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

**New command** (fixed):
```bash
celery -A celery_worker.celery_app worker --loglevel=info --pool=solo
```

The `celery_worker.py` module ensures:
- ✅ Proper Python path setup
- ✅ Flask app context available to tasks
- ✅ Environment variables loaded
- ✅ All app modules importable

## Expected Output

You should see:
```
-------------- celery@YOUR-PC v5.3.4 (emerald-rush)
--- ***** -----
-- ******* ---- Windows-10-... 2026-02-14 21:XX:XX
- *** --- * ---
- ** ---------- [config]
- ** ---------- .> app:         image_converter:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/1
- *** --- * --- .> concurrency: 4 (solo)
-- ******* ----
--- ***** -----
 -------------- [queues]
                .> conversions      exchange=conversions(direct) key=conversion.#
                .> cleanup          exchange=cleanup(direct) key=cleanup.#

[tasks]
  . app.tasks.cleanup_tasks.cleanup_failed_uploads
  . app.tasks.cleanup_tasks.cleanup_old_files
  . app.tasks.cleanup_tasks.cleanup_task_files
  . app.tasks.conversion_tasks.convert_batch_images
  . app.tasks.conversion_tasks.convert_single_image
  . app.tasks.conversion_tasks.create_zip_archive

[2026-02-14 21:XX:XX,XXX: INFO/MainProcess] Connected to redis://localhost:6379/0
[2026-02-14 21:XX:XX,XXX: INFO/MainProcess] mingle: searching for neighbors
[2026-02-14 21:XX:XX,XXX: INFO/MainProcess] mingle: all alone
[2026-02-14 21:XX:XX,XXX: INFO/MainProcess] celery@YOUR-PC ready.
```

## Test It Works

1. **Upload an image** at http://localhost:5000

2. **Check the worker logs** - you should see:
   ```
   [2026-02-14 21:XX:XX,XXX: INFO/MainProcess] Task app.tasks.conversion_tasks.convert_batch_images[abc-123...] received
   [2026-02-14 21:XX:XX,XXX: INFO/MainProcess] Task app.tasks.conversion_tasks.convert_batch_images[abc-123...] succeeded in 2.5s
   ```

3. **No errors!** - The conversion should complete successfully

## If You Still Get Errors

Check that:
- ✅ Flask app is running (`python run.py`)
- ✅ Redis is running (`docker ps` or `redis-cli ping`)
- ✅ You're in the correct directory
- ✅ Virtual environment is activated (if using one)
- ✅ All dependencies installed (`pip install -r requirements.txt`)

## Optional: Start Celery Beat

For automatic cleanup every 15 minutes:

```bash
celery -A celery_worker.celery_app beat --loglevel=info
```

---

**The fix**: Created [celery_worker.py](celery_worker.py) to properly initialize Flask context for Celery tasks.
