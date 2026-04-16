#!/usr/bin/env python3
"""
SignMeet Flask Setup Script
Automated setup for the SignMeet Flask application
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, check=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_python_version():
    """Check if Python version is adequate"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def create_directory_structure():
    """Create necessary directories"""
    directories = [
        'templates',
        'static/css',
        'static/js',
        'static/images',
        'models'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_virtual_environment():
    """Set up Python virtual environment"""
    venv_name = "signmeet_env"
    
    if Path(venv_name).exists():
        print(f"✅ Virtual environment '{venv_name}' already exists")
        return True
    
    print(f"Creating virtual environment: {venv_name}")
    success, stdout, stderr = run_command(f"python -m venv {venv_name}")
    
    if success:
        print(f"✅ Created virtual environment: {venv_name}")
        return True
    else:
        print(f"❌ Failed to create virtual environment: {stderr}")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("Installing dependencies from requirements.txt...")
    
    # Determine activation script
    if os.name == 'nt':  # Windows
        activate_script = "signmeet_env\\Scripts\\activate"
        pip_cmd = "signmeet_env\\Scripts\\pip"
    else:  # macOS/Linux
        activate_script = "source signmeet_env/bin/activate"
        pip_cmd = "signmeet_env/bin/pip"
    
    success, stdout, stderr = run_command(f"{pip_cmd} install -r requirements.txt")
    
    if success:
        print("✅ Dependencies installed successfully")
        return True
    else:
        print(f"❌ Failed to install dependencies: {stderr}")
        return False

def setup_environment_file():
    """Set up environment variables"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        
        # Generate a random secret key
        import secrets
        secret_key = secrets.token_urlsafe(32)
        
        # Read and replace secret key in .env file
        with open(env_file, 'r') as f:
            content = f.read()
        
        content = content.replace(
            'your-super-secret-key-change-this-in-production',
            secret_key
        )
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ Generated random SECRET_KEY")
        return True
    else:
        print("❌ .env.example file not found")
        return False

def check_model_files():
    """Check for ML model files"""
    model_file = Path('models/sign_model.h5')
    labels_file = Path('models/labels.joblib')
    
    if model_file.exists() and labels_file.exists():
        print("✅ ML model files found")
        print("   - Sign language recognition will be enabled")
        return True
    else:
        print("⚠️  ML model files not found")
        print("   - Place 'sign_model.h5' and 'labels.joblib' in models/ directory")
        print("   - App will run without sign recognition features")
        return False

def test_installation():
    """Test the Flask application"""
    print("\nTesting Flask application...")
    
    # Try importing required modules
    try:
        import flask
        import flask_socketio
        import cv2
        import numpy
        import tensorflow
        print("✅ All required modules can be imported")
    except ImportError as e:
        print(f"❌ Missing module: {e}")
        return False
    
    # Test basic app creation
    try:
        from app import app
        print("✅ Flask app can be created")
        return True
    except Exception as e:
        print(f"❌ Failed to create Flask app: {e}")
        return False

def print_instructions():
    """Print final instructions"""
    print("\n" + "="*60)
    print("🎉 SignMeet Flask setup completed!")
    print("="*60)
    
    print("\n📋 Next steps:")
    print("1. Activate virtual environment:")
    if os.name == 'nt':  # Windows
        print("   signmeet_env\\Scripts\\activate")
    else:  # macOS/Linux
        print("   source signmeet_env/bin/activate")
    
    print("\n2. Run the application:")
    print("   python app.py")
    
    print("\n3. Open in browser:")
    print("   http://localhost:5000")
    
    print("\n4. For remote testing with ngrok:")
    print("   - Install ngrok: npm install -g ngrok")
    print("   - Run: ngrok http 5000")
    print("   - Share the HTTPS URL with others")
    
    print("\n5. Optional: Add ML models for sign recognition")
    print("   - Place sign_model.h5 in models/")
    print("   - Place labels.joblib in models/")
    
    print("\n📖 For more information, see README.md")
    print("="*60)

def main():
    """Main setup function"""
    print("🚀 SignMeet Flask Setup")
    print("="*40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directory structure
    create_directory_structure()
    
    # Setup virtual environment
    if not setup_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup environment file
    if not setup_environment_file():
        sys.exit(1)
    
    # Check model files
    check_model_files()
    
    # Test installation
    if not test_installation():
        print("\n⚠️  Setup completed but with errors")
        print("Please check the error messages above")
    
    # Print final instructions
    print_instructions()

if __name__ == "__main__":
    main()