"""
Configuration for SignMeet Flask Application
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Model paths
    MODEL_PATH = os.environ.get('MODEL_PATH', 'models/sign_model.h5')
    LABELS_PATH = os.environ.get('LABELS_PATH', 'models/labels.joblib')
    
    # ML Model settings
    CONFIDENCE_THRESHOLD = float(os.environ.get('CONFIDENCE_THRESHOLD', '0.7'))
    MAX_PARTICIPANTS_PER_ROOM = int(os.environ.get('MAX_PARTICIPANTS_PER_ROOM', '6'))
    
    # WebRTC settings
    STUN_SERVERS = [
        'stun:stun.l.google.com:19302',
        'stun:stun1.l.google.com:19302'
    ]
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENV = 'production'
    
    # Use secure settings in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}