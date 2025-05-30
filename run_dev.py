#!/usr/bin/env python3
"""
Alternative approach using uvicorn's built-in reload with custom patterns
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_includes=["*.py", "*.csv"],  # Watch both Python and CSV files
        reload_dirs=["./"],  # Watch current directory and subdirectories
        log_level="info"
    )
