#!/usr/bin/env python3
"""
Restart script to clear sessions and restart the application
"""
import os
import sys
import subprocess
import time

def clear_sessions():
    """Clear Flask session files"""
    try:
        # Clear any session files
        session_files = [
            'flask_session',
            'sessions',
            '.flask_session'
        ]
        
        for session_dir in session_files:
            if os.path.exists(session_dir):
                import shutil
                shutil.rmtree(session_dir)
                print(f"Cleared session directory: {session_dir}")
        
        print("Session cache cleared successfully")
    except Exception as e:
        print(f"Error clearing sessions: {e}")

def restart_application():
    """Restart the application"""
    try:
        print("Stopping any running instances...")
        
        # Kill any existing Python processes running the app
        try:
            subprocess.run(['taskkill', '/f', '/im', 'python.exe'], 
                         capture_output=True, check=False)
        except:
            pass
        
        time.sleep(2)
        
        print("Starting application...")
        subprocess.Popen([sys.executable, 'run.py'])
        print("Application restarted successfully!")
        
    except Exception as e:
        print(f"Error restarting application: {e}")

if __name__ == "__main__":
    print("=== Restarting Customer Sentiment Alert System ===")
    clear_sessions()
    restart_application()
    print("=== Restart Complete ===")
    print("Access the application at: http://localhost:5000")
