#!/usr/bin/env python
"""
Setup script for PaperLit application.
This script will set up the necessary directories and dependencies.
"""
import os
import sys
import subprocess
from setup_pdfjs import download_pdfjs

def setup_paperlit():
    """Set up the PaperLit application."""
    print("Setting up PaperLit application...")
    
    # Create necessary directories
    directories = [
        "uploads",
        "src/static",
        "src/static/images",
        "instance"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Install Python dependencies
    print("Installing Python dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Download and set up PDF.js
    download_pdfjs()
    
    print("\nPaperLit setup completed successfully!")
    print("\nTo run the application:")
    print("1. Activate your virtual environment (if using one)")
    print("2. Run: python -m flask --app src.app run --debug")

if __name__ == "__main__":
    setup_paperlit()
