#!/bin/bash

# SignMeet Flask Quick Start Script
# This script sets up and runs the SignMeet Flask application

set -e  # Exit on any error

echo "🚀 SignMeet Flask Quick Start"
echo "==============================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "signmeet_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv signmeet_env
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source signmeet_env/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        # Generate random secret key
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i.bak "s/your-super-secret-key-change-this-in-production/$SECRET_KEY/" .env
        rm .env.bak
        echo "✅ Created .env file with random SECRET_KEY"
    else
        echo "⚠️  .env.example not found, creating basic .env"
        cat > .env << EOF
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
FLASK_ENV=development
FLASK_DEBUG=True
HOST=0.0.0.0
PORT=5000
EOF
    fi
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
mkdir -p models static/css static/js static/images templates
echo "✅ Created necessary directories"

# Check for model files
if [ -f "models/sign_model.h5" ] && [ -f "models/labels.joblib" ]; then
    echo "✅ ML model files found - sign recognition will be enabled"
else
    echo "⚠️  ML model files not found - app will run without sign recognition"
    echo "   Place sign_model.h5 and labels.joblib in the models/ directory to enable this feature"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "🚀 Starting Flask application..."
echo "   Access the app at: http://localhost:5000"
echo "   Press Ctrl+C to stop the server"
echo ""

# Run the application
python app.py