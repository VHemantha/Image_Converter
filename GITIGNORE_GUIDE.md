# .gitignore Configuration Guide

## What's Ignored

### Python Generated Files
- `__pycache__/` - Python bytecode cache
- `*.pyc, *.pyo, *.pyd` - Compiled Python files
- `*.egg-info/` - Package metadata
- `.pytest_cache/` - Pytest cache

### Virtual Environments
- `venv/`, `env/`, `.venv/` - Virtual environment directories
- All standard Python environment folders

### Environment Files
- `.env` - **Your secrets (NEVER commit!)**
- `.env.local` - Local overrides
- `.env.production` - Production secrets
- ✅ `.env.example` - **Kept** (template for others)

### Application Data
- `temp/` contents - Uploaded and converted images
- `logs/` contents - Application log files
- ✅ `temp/.gitkeep` - **Kept** (preserves folder structure)
- ✅ `temp/uploads/.gitkeep` - **Kept**
- ✅ `temp/converted/.gitkeep` - **Kept**
- ✅ `logs/.gitkeep` - **Kept**

### OS & IDE Files
- `nul` - Windows artifact
- `.DS_Store` - macOS metadata
- `Thumbs.db` - Windows thumbnails
- `.vscode/` - VS Code settings (optional)
- `.idea/` - PyCharm settings

### Docker Volumes
- `redis_data/` - Redis data persists in Docker named volumes

### Test Files
- `test_*.jpg, test_*.png` - Test images
- `*.test.*` - Test files

## What's Included

### Application Code
✅ All `.py` files in `app/` directory
✅ All subdirectories: `app/static/`, `app/templates/`, `app/tasks/`, `app/utils/`
✅ `__init__.py` files (preserve module structure)

### Configuration
✅ `requirements.txt` - Python dependencies
✅ `.env.example` - Environment template
✅ `run.py` - Entry point
✅ `celery_worker.py` - Celery entry point

### Docker Files
✅ `Dockerfile` - Container definition
✅ `docker-compose.yml` - Service orchestration
✅ `.dockerignore` - Build optimization

### Documentation
✅ All `*.md` files (README, guides, etc.)
✅ Phase documentation (PHASE2_SETUP.md, PHASE3_FEATURES.md, etc.)

### Static Assets
✅ `app/static/css/` - Stylesheets
✅ `app/static/js/` - JavaScript files
✅ Templates in `app/templates/`

### Directory Structure
✅ Empty directories with `.gitkeep` files
✅ Folder hierarchy preserved

## Folder Structure in Git

```
Image_Converter/
├── .dockerignore              ✅ Included
├── .env.example              ✅ Included
├── .env                      ❌ Ignored (secrets)
├── .gitignore                ✅ Included
├── Dockerfile                ✅ Included
├── docker-compose.yml        ✅ Included
├── requirements.txt          ✅ Included
├── run.py                    ✅ Included
├── celery_worker.py          ✅ Included
├── app/
│   ├── __init__.py           ✅ Included
│   ├── config.py             ✅ Included
│   ├── forms.py              ✅ Included
│   ├── routes.py             ✅ Included
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css    ✅ Included
│   │   └── js/
│   │       └── main.js       ✅ Included
│   ├── templates/
│   │   ├── base.html         ✅ Included
│   │   └── index.html        ✅ Included
│   ├── tasks/
│   │   ├── __init__.py       ✅ Included
│   │   ├── celery_app.py     ✅ Included
│   │   ├── celery_config.py  ✅ Included
│   │   ├── conversion_tasks.py ✅ Included
│   │   └── cleanup_tasks.py  ✅ Included
│   └── utils/
│       ├── __init__.py       ✅ Included
│       ├── file_validator.py ✅ Included
│       └── image_converter.py ✅ Included
├── temp/
│   ├── .gitkeep              ✅ Included (preserves structure)
│   ├── uploads/
│   │   ├── .gitkeep          ✅ Included
│   │   └── *.jpg             ❌ Ignored (temporary files)
│   └── converted/
│       ├── .gitkeep          ✅ Included
│       └── *.webp            ❌ Ignored (temporary files)
├── logs/
│   ├── .gitkeep              ✅ Included (preserves structure)
│   └── *.log                 ❌ Ignored (log files)
├── venv/                     ❌ Ignored (virtual environment)
└── __pycache__/              ❌ Ignored (Python cache)
```

## How It Works

### Pattern Explanation

```gitignore
# Ignore everything in temp/
temp/*

# But keep the .gitkeep file
!temp/.gitkeep

# And keep the uploads directory itself
!temp/uploads/

# But ignore everything in uploads/
temp/uploads/*

# Except the .gitkeep
!temp/uploads/.gitkeep
```

**Result**:
- Folder structure preserved
- Actual files ignored
- Clean repository

### Why Use .gitkeep?

Git doesn't track empty directories. `.gitkeep` is a convention (any filename works) to:
1. Preserve directory structure
2. Ensure directories exist on clone
3. Document folder purpose

## Verification

### Check what's ignored:
```bash
git status --ignored
```

### Check what will be committed:
```bash
git add -n .
```

### See effective gitignore rules:
```bash
git check-ignore -v <filename>
```

## Common Scenarios

### "I accidentally committed .env"
```bash
# Remove from git but keep locally
git rm --cached .env
git commit -m "Remove .env from repository"

# Make sure .env is in .gitignore
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Update .gitignore"
```

### "I want to commit a specific test file"
```bash
# Force add despite .gitignore
git add -f test_important.jpg

# Or exclude from .gitignore:
# In .gitignore, add:
!test_important.jpg
```

### "Folder structure not preserved after clone"
```bash
# Add .gitkeep files:
touch temp/uploads/.gitkeep
touch temp/converted/.gitkeep
touch logs/.gitkeep

git add temp/**/.gitkeep logs/.gitkeep
git commit -m "Preserve directory structure"
```

## Best Practices

### ✅ DO:
- Keep `.env.example` with dummy values
- Add `.gitkeep` to empty directories you need
- Ignore all secrets and credentials
- Ignore generated files (logs, cache, temp)
- Document what's ignored and why

### ❌ DON'T:
- Commit `.env` files with secrets
- Commit virtual environments
- Commit temporary or generated files
- Commit OS-specific files (.DS_Store, Thumbs.db)
- Commit IDE-specific settings (unless team agreed)

## Project-Specific Rules

### Image Converter Specifics

**Always Ignored:**
- Uploaded images in `temp/uploads/`
- Converted images in `temp/converted/`
- Application logs in `logs/`
- Environment variables in `.env`

**Always Included:**
- All application code
- Documentation files
- Configuration templates
- Docker files
- Static assets
- Directory structure (.gitkeep files)

## Troubleshooting

### Problem: Files still showing up despite .gitignore
**Solution:** Remove from cache and re-add
```bash
git rm -r --cached .
git add .
git commit -m "Apply .gitignore rules"
```

### Problem: Directory not preserved after clone
**Solution:** Add .gitkeep file
```bash
touch <directory>/.gitkeep
git add <directory>/.gitkeep
git commit -m "Preserve directory structure"
```

### Problem: Accidentally committed secrets
**Solution:** Remove from history
```bash
# Simple case (recent commit):
git reset --soft HEAD~1
git reset HEAD .env
git commit -m "Remove secrets"

# Complex case (old commit):
# Use git-filter-repo or BFG Repo-Cleaner
# Then change the exposed secrets!
```

---

**Last Updated:** Phase 3 Implementation
**Maintained By:** Image Converter Project
**Reference:** [.gitignore](.gitignore)
