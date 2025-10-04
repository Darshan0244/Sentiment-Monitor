#!/usr/bin/env python3
"""
Main entry point for the Customer Sentiment Alert System
"""
import sys
import os
import threading
import time
from loguru import logger

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from sentiment_monitor import SentimentMonitor
from app import app

def main():
    """Main function to start both the web dashboard and monitoring system"""
    config = Config()
    
    # Setup logging
    logger.add(
        config.LOG_FILE,
        rotation="1 day",
        retention="30 days",
        level=config.LOG_LEVEL
    )
    
    logger.info("Starting Customer Sentiment Alert System")
    
    # Initialize and start the monitoring system
    monitor = SentimentMonitor(config)
    
    # Start monitoring in a separate thread
    monitor_thread = threading.Thread(target=monitor.start_monitoring, daemon=True)
    monitor_thread.start()
    
    logger.info("Monitoring system started")
    
    # Start the web dashboard
    logger.info("Starting web dashboard on http://localhost:5000")
    app.run(debug=config.DEBUG, host='0.0.0.0', port=5000, use_reloader=False)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down Customer Sentiment Alert System")
    except Exception as e:
        logger.error(f"Error starting system: {e}")
        sys.exit(1)
