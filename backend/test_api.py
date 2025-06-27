from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI(title="Test API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Test API is working", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "port": os.environ.get("PORT", "unknown"),
        "pythonpath": os.environ.get("PYTHONPATH", "unknown")
    }

@app.get("/debug")
async def debug():
    import sys
    return {
        "python_version": sys.version,
        "python_path": sys.path,
        "env_vars": dict(os.environ),
        "cwd": os.getcwd()
    } 