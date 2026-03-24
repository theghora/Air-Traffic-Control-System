import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///atc_system.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ATC System Configuration
    MAX_RUNWAY_CAPACITY = 1  # One aircraft per runway at a time
    RUNWAY_COOLDOWN_SECONDS = 1  # Time before runway can be reused

    # Runway Length Requirements (in meters)
    RUNWAY_LENGTH_SMALL = 1500
    RUNWAY_LENGTH_MEDIUM = 2500
    RUNWAY_LENGTH_HEAVY = 3500

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
