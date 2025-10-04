"""
Configuration settings for the Customer Sentiment Alert System
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///sentiment_alerts.db')
    
    # Email configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    ALERT_EMAIL = os.getenv('ALERT_EMAIL', 'support@company.com')
    
    # Social Media API Keys
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY', '')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET', '')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', '')
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', '')
    
    # Monitoring configuration
    MONITORING_INTERVAL = int(os.getenv('MONITORING_INTERVAL', '300'))  # 5 minutes
    SENTIMENT_THRESHOLD = float(os.getenv('SENTIMENT_THRESHOLD', '-0.3'))  # Negative threshold
    
    # Keywords to monitor
    MONITOR_KEYWORDS = [
        'customer service', 'support', 'complaint', 'issue', 'problem',
        'refund', 'cancel', 'dissatisfied', 'terrible', 'awful', 'horrible',
        'worst', 'hate', 'disappointed', 'frustrated', 'angry'
    ]
    
    # Company/brand names to monitor
    COMPANY_NAMES = [
        'YourCompany', 'YourBrand', 'YourProduct'
    ]
    
    # Review sites to monitor
    REVIEW_SITES = [
        'trustpilot.com',
        'yelp.com',
        'google.com/maps',
        'amazon.com',
        'reddit.com'
    ]
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'sentiment_alerts.log')
