"""
Main sentiment monitoring and alerting system
"""
import time
import threading
import schedule
from datetime import datetime, timedelta
from loguru import logger
from typing import List, Dict
import json

from config import Config
from sentiment_analyzer import SentimentAnalyzer
from web_scraper import WebScraper
from database import SentimentDatabase
from email_notifier import EmailNotifier

class SentimentMonitor:
    def __init__(self, config: Config):
        """Initialize the sentiment monitoring system"""
        self.config = config
        self.sentiment_analyzer = SentimentAnalyzer()
        self.web_scraper = WebScraper(config)
        self.database = SentimentDatabase()
        self.email_notifier = EmailNotifier(config)
        
        self.is_running = False
        self.monitoring_thread = None
        
        # Setup logging
        logger.add(
            config.LOG_FILE,
            rotation="1 day",
            retention="30 days",
            level=config.LOG_LEVEL
        )
        
        logger.info("Sentiment Monitor initialized")
    
    def start_monitoring(self):
        """Start the monitoring system"""
        if self.is_running:
            logger.warning("Monitoring is already running")
            return
        
        self.is_running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Schedule daily summary email
        schedule.every().day.at("09:00").do(self._send_daily_summary)
        
        # Schedule database cleanup
        schedule.every().week.do(self._cleanup_old_data)
        
        logger.info("Sentiment monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        self.web_scraper.close()
        self.database.close()
        
        logger.info("Sentiment monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                logger.info("Starting monitoring cycle")
                
                # Scrape data from all sources
                scraped_data = self.web_scraper.scrape_all_sources()
                
                if scraped_data:
                    # Analyze sentiment for all scraped data
                    analyzed_data = self._analyze_scraped_data(scraped_data)
                    
                    # Process alerts for negative sentiment
                    self._process_alerts(analyzed_data)
                
                # Run scheduled tasks
                schedule.run_pending()
                
                logger.info(f"Monitoring cycle completed. Sleeping for {self.config.MONITORING_INTERVAL} seconds")
                time.sleep(self.config.MONITORING_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _analyze_scraped_data(self, scraped_data: List[Dict]) -> List[Dict]:
        """Analyze sentiment for scraped data"""
        analyzed_data = []
        
        for item in scraped_data:
            try:
                # Analyze sentiment
                sentiment_result = self.sentiment_analyzer.analyze_sentiment(
                    item.get('text', ''),
                    item.get('source', '')
                )
                
                # Add original data to sentiment result
                sentiment_result.update({
                    'url': item.get('url', ''),
                    'author': item.get('author', ''),
                    'timestamp': item.get('timestamp', datetime.now().isoformat()),
                    'metadata': {
                        'rating': item.get('rating'),
                        'retweet_count': item.get('retweet_count'),
                        'favorite_count': item.get('favorite_count'),
                        'score': item.get('score'),
                        'subreddit': item.get('subreddit')
                    }
                })
                
                # Store in database
                sentiment_id = self.database.insert_sentiment_analysis(sentiment_result)
                sentiment_result['id'] = sentiment_id
                
                analyzed_data.append(sentiment_result)
                
            except Exception as e:
                logger.error(f"Error analyzing sentiment for item: {e}")
                continue
        
        logger.info(f"Analyzed {len(analyzed_data)} items")
        return analyzed_data
    
    def _process_alerts(self, analyzed_data: List[Dict]):
        """Process alerts for negative sentiment"""
        negative_items = [item for item in analyzed_data if item.get('is_negative', False)]
        
        if not negative_items:
            logger.info("No negative sentiment detected in this cycle")
            return
        
        logger.info(f"Processing {len(negative_items)} negative sentiment items")
        
        for item in negative_items:
            try:
                # Check if we should create an alert
                if self._should_create_alert(item):
                    # Generate response recommendation
                    response_recommendation = self.email_notifier.generate_response_recommendation(item)
                    
                    # Create alert
                    alert_id = self.database.create_alert(
                        sentiment_id=item['id'],
                        alert_type='negative_sentiment',
                        urgency_level=item.get('urgency_level', 'medium'),
                        message=f"Negative sentiment detected from {item.get('source', 'unknown')}",
                        response_recommendation=response_recommendation
                    )
                    
                    # Send email alert
                    alert_data = {
                        'id': alert_id,
                        'urgency_level': item.get('urgency_level', 'medium'),
                        'response_recommendation': response_recommendation
                    }
                    
                    email_sent = self.email_notifier.send_alert_email(alert_data, item)
                    
                    if email_sent:
                        self.database.mark_alert_email_sent(alert_id)
                        logger.info(f"Alert {alert_id} created and email sent")
                    else:
                        logger.error(f"Failed to send email for alert {alert_id}")
                
            except Exception as e:
                logger.error(f"Error processing alert for item: {e}")
                continue
    
    def _should_create_alert(self, item: Dict) -> bool:
        """Determine if an alert should be created for this item"""
        sentiment_score = item.get('sentiment_score', 0)
        confidence = item.get('confidence', 0)
        urgency_level = item.get('urgency_level', 'low')
        
        # Create alert if sentiment is below threshold and confidence is high enough
        if sentiment_score < self.config.SENTIMENT_THRESHOLD and confidence > 0.6:
            return True
        
        # Create alert for high urgency items regardless of score
        if urgency_level in ['critical', 'high']:
            return True
        
        return False
    
    def _send_daily_summary(self):
        """Send daily summary email"""
        try:
            # Get statistics for the last 24 hours
            stats = self.database.get_sentiment_statistics(days=1)
            
            # Get recent critical alerts
            critical_alerts = self.database.get_active_alerts('critical')
            
            # Prepare summary data
            summary_data = {
                'total_mentions': sum(item['count'] for item in stats.get('sentiment_distribution', [])),
                'negative_mentions': sum(
                    item['count'] for item in stats.get('sentiment_distribution', [])
                    if item['sentiment_category'] in ['negative', 'very_negative']
                ),
                'total_alerts': stats.get('alert_statistics', {}).get('total_alerts', 0),
                'critical_alerts': len([alert for alert in critical_alerts if alert.get('urgency_level') == 'critical']),
                'high_alerts': len([alert for alert in critical_alerts if alert.get('urgency_level') == 'high']),
                'top_sources': stats.get('source_distribution', [])[:5],
                'recent_critical': critical_alerts[:5]
            }
            
            # Send summary email
            self.email_notifier.send_daily_summary(summary_data)
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old data from database"""
        try:
            self.database.cleanup_old_data(days=30)
            logger.info("Database cleanup completed")
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")
    
    def get_current_alerts(self, urgency_level: str = None) -> List[Dict]:
        """Get current active alerts"""
        return self.database.get_active_alerts(urgency_level)
    
    def get_sentiment_statistics(self, days: int = 7) -> Dict:
        """Get sentiment statistics"""
        return self.database.get_sentiment_statistics(days)
    
    def test_system(self) -> Dict:
        """Test all system components"""
        test_results = {
            'sentiment_analyzer': False,
            'web_scraper': False,
            'database': False,
            'email_notifier': False
        }
        
        try:
            # Test sentiment analyzer
            test_text = "This is a terrible product and I hate it!"
            result = self.sentiment_analyzer.analyze_sentiment(test_text)
            test_results['sentiment_analyzer'] = result.get('is_negative', False)
            
            # Test database
            test_results['database'] = True  # Database connection is tested during init
            
            # Test email notifier
            test_results['email_notifier'] = self.email_notifier.test_email_connection()
            
            # Test web scraper (basic test)
            test_results['web_scraper'] = self.web_scraper.driver is not None
            
        except Exception as e:
            logger.error(f"Error during system test: {e}")
        
        return test_results
    
    def manual_scan(self, company_name: str = None) -> Dict:
        """Perform a manual scan for a specific company"""
        try:
            if company_name:
                companies = [company_name]
            else:
                companies = self.config.COMPANY_NAMES
            
            logger.info(f"Starting manual scan for: {companies}")
            
            # Scrape data
            scraped_data = []
            for company in companies:
                company_data = self.web_scraper.scrape_all_sources([company])
                scraped_data.extend(company_data)
            
            # Analyze sentiment
            analyzed_data = self._analyze_scraped_data(scraped_data)
            
            # Process alerts
            self._process_alerts(analyzed_data)
            
            return {
                'success': True,
                'companies_scanned': companies,
                'items_found': len(scraped_data),
                'items_analyzed': len(analyzed_data),
                'negative_items': len([item for item in analyzed_data if item.get('is_negative', False)])
            }
            
        except Exception as e:
            logger.error(f"Error during manual scan: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Global monitor instance
monitor = None

def get_monitor() -> SentimentMonitor:
    """Get the global monitor instance"""
    global monitor
    if monitor is None:
        config = Config()
        monitor = SentimentMonitor(config)
    return monitor

if __name__ == "__main__":
    # Test the system
    config = Config()
    monitor = SentimentMonitor(config)
    
    # Run system test
    test_results = monitor.test_system()
    print("System Test Results:")
    for component, status in test_results.items():
        print(f"  {component}: {'✅' if status else '❌'}")
    
    # Start monitoring
    monitor.start_monitoring()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop_monitoring()
