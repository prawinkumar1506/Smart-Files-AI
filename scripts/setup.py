#!/usr/bin/env python3
"""
Setup script for SmartFile AI backend dependencies
"""

import subprocess
import sys
import os

def install_requirements():
    """Install Python requirements"""
    requirements_file = os.path.join(os.path.dirname(__file__), '..', 'backend', 'requirements.txt')
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', requirements_file
        ])
        print("✅ Python dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Python dependencies: {e}")
        return False
    
    return True

def download_models():
    """Download required ML models"""
    try:
        import sentence_transformers
        
        # Download the embedding model
        model = sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model downloaded successfully")
        
        return True
    except Exception as e:
        print(f"❌ Error downloading models: {e}")
        return False

def main():
    print("🚀 Setting up SmartFile AI...")
    
    if not install_requirements():
        sys.exit(1)
    
    if not download_models():
        sys.exit(1)
    
    print("✅ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Run 'npm install' to install frontend dependencies")
    print("2. Run 'npm run electron-dev' to start the application")

if __name__ == "__main__":
    main()
