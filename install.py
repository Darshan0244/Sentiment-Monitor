#!/usr/bin/env python3
"""
Installation script for the Customer Sentiment Alert System
"""
import subprocess
import sys
import os
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"[INFO] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"[SUCCESS] {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("[ERROR] Python 3.8 or higher is required")
        return False
    print(f"[SUCCESS] Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install Python dependencies"""
    # Try lite version first to avoid space issues
    if os.path.exists('requirements_lite.txt'):
        print("[INFO] Using lightweight requirements to avoid space issues...")
        return run_command("pip install -r requirements_lite.txt", "Installing Python dependencies (lite)")
    else:
        return run_command("pip install -r requirements.txt", "Installing Python dependencies")

def download_nltk_data():
    """Download required NLTK data"""
    try:
        import nltk
        print("[INFO] Downloading NLTK data...")
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        print("[SUCCESS] NLTK data downloaded successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to download NLTK data: {e}")
        return False

def check_chromedriver():
    """Check if ChromeDriver is available"""
    try:
        result = subprocess.run("chromedriver --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("[SUCCESS] ChromeDriver is available")
            return True
    except:
        pass
    
    print("[WARNING] ChromeDriver not found")
    print("Please install ChromeDriver:")
    print("1. Download from: https://chromedriver.chromium.org/")
    print("2. Add to your system PATH")
    print("3. Or place chromedriver.exe in this directory")
    return False

def create_env_file():
    """Create .env file from template"""
    if os.path.exists('.env'):
        print("[SUCCESS] .env file already exists")
        return True
    
    if os.path.exists('env_example.txt'):
        try:
            with open('env_example.txt', 'r') as src:
                content = src.read()
            with open('.env', 'w') as dst:
                dst.write(content)
            print("[SUCCESS] Created .env file from template")
            print("[WARNING] Please edit .env file with your actual configuration")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to create .env file: {e}")
            return False
    else:
        print("[ERROR] env_example.txt not found")
        return False

def main():
    """Main installation function"""
    print("Customer Sentiment Alert System - Installation")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("[ERROR] Installation failed at dependency installation")
        sys.exit(1)
    
    # Download NLTK data
    if not download_nltk_data():
        print("[WARNING] NLTK data download failed, but installation can continue")
    
    # Check ChromeDriver
    chromedriver_ok = check_chromedriver()
    
    # Create .env file
    if not create_env_file():
        print("[ERROR] Failed to create .env file")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("[SUCCESS] Installation completed!")
    print("\nNext steps:")
    print("1. Edit .env file with your email and API credentials")
    print("2. Update config.py with your company names and keywords")
    if not chromedriver_ok:
        print("3. Install ChromeDriver for web scraping")
    print("4. Run: python run.py")
    print("\nFor help, see README.md")

if __name__ == "__main__":
    main()
