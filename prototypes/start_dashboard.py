#!/usr/bin/env python3
"""
Start Dashboard - Handles all setup and launches dashboard
"""

import sys
import subprocess
from pathlib import Path

def check_and_install_dependencies():
    """Check if dependencies are installed, install if missing"""
    try:
        import streamlit
        import sentence_transformers
        import chromadb
        import crewai
        print("✅ All dependencies found")
        return True
    except ImportError as e:
        print(f"⚠️  Missing dependency: {e}")
        print("📦 Installing dependencies...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-q", 
                "-r", "requirements.txt"
            ])
            print("✅ Dependencies installed!")
            return True
        except Exception as install_error:
            print(f"❌ Failed to install: {install_error}")
            print("\nPlease run manually:")
            print("  pip install -r requirements.txt")
            return False

def check_env_file():
    """Check if .env file exists"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  No .env file found. Creating template...")
        env_file.write_text("OPENAI_API_KEY=your_key_here\n")
        print("✅ Created .env file")
        print("⚠️  IMPORTANT: Edit .env and add your OpenAI API key!")
        return False
    return True

def main():
    print("🛡️  Cyber Defense Simulator Dashboard")
    print("=" * 50)
    
    # Check dependencies
    if not check_and_install_dependencies():
        sys.exit(1)
    
    # Check .env
    check_env_file()
    
    # Get dashboard path
    dashboard_path = Path(__file__).parent / "cyber_defense_simulator" / "dashboard" / "dashboard.py"
    
    if not dashboard_path.exists():
        print(f"❌ Dashboard not found at {dashboard_path}")
        sys.exit(1)
    
    print("\n🚀 Starting dashboard...")
    print("   URL: http://localhost:8501")
    print("   Press Ctrl+C to stop\n")
    
    # Run streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(dashboard_path),
            "--server.headless", "true"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped")

if __name__ == "__main__":
    main()

