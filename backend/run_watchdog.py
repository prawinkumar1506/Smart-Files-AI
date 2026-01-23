#!/usr/bin/env python3
"""
Script to run the watchdog service for auto-reloading the backend.
"""

import os
import sys
import subprocess
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_watchdog():
    """Install watchdog if not already installed"""
    try:
        import watchdog
        logger.info("watchdog is already installed")
    except ImportError:
        logger.info("Installing watchdog...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "watchdog"])
        logger.info("watchdog installed successfully")

def run_watchdog():
    """Run the watchdog service"""
    # Install watchdog if needed
    install_watchdog()

    # Get the directory of this script
    backend_dir = os.path.dirname(os.path.abspath(__file__))

    # Run the watchdog
    logger.info(f"Starting watchdog in {backend_dir}")
    subprocess.call([sys.executable, os.path.join(backend_dir, "watchdog.py"), backend_dir])

if __name__ == "__main__":
    run_watchdog()
