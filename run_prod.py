#!/usr/bin/env python3
"""
Production server configuration for Render with CSV file watching
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=10000,         # Render's port
        reload=True,        # Enable auto-reload in production
        reload_includes=["*.py", "*.csv"],  # Watch both Python and CSV files
        reload_dirs=["./"],  # Watch current directory and subdirectories
        log_level="info"
    )
