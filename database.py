"""
Database management for storing sentiment analysis results and alerts
"""
import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
from typing import List, Dict, Optional
import os

class SentimentDatabase:
    def __init__(self, db_path: str = "sentiment_alerts.db"):
        """Initialize the database connection"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create sentiment_analysis table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sentiment_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        text TEXT NOT NULL,
                        sentiment_score REAL NOT NULL,
                        sentiment_category TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        is_negative BOOLEAN NOT NULL,
                        urgency_level TEXT NOT NULL,
                        source TEXT NOT NULL,
                        source_url TEXT,
                        author TEXT,
                        timestamp TEXT NOT NULL,
                        analysis_timestamp TEXT NOT NULL,
                        vader_score REAL,
                        textblob_score REAL,
                        transformer_score REAL,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create alerts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sentiment_id INTEGER NOT NULL,
                        alert_type TEXT NOT NULL,
                        urgency_level TEXT NOT NULL,
                        message TEXT NOT NULL,
                        email_sent BOOLEAN DEFAULT FALSE,
                        email_sent_at TIMESTAMP,
                        response_recommendation TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (sentiment_id) REFERENCES sentiment_analysis (id)
                    )
                ''')
                
                # Create monitoring_config table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS monitoring_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_name TEXT NOT NULL,
                        keywords TEXT NOT NULL,
                        sources TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create email_logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS email_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id INTEGER NOT NULL,
                        recipient_email TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        body TEXT NOT NULL,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (alert_id) REFERENCES alerts (id)
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sentiment_timestamp ON sentiment_analysis(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sentiment_score ON sentiment_analysis(sentiment_score)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sentiment_source ON sentiment_analysis(source)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_urgency ON alerts(urgency_level)')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def insert_sentiment_analysis(self, analysis_result: Dict) -> int:
        """Insert sentiment analysis result into database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO sentiment_analysis (
                        text, sentiment_score, sentiment_category, confidence,
                        is_negative, urgency_level, source, source_url, author,
                        timestamp, analysis_timestamp, vader_score, textblob_score,
                        transformer_score, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis_result.get('text', ''),
                    analysis_result.get('sentiment_score', 0.0),
                    analysis_result.get('sentiment_category', 'neutral'),
                    analysis_result.get('confidence', 0.0),
                    analysis_result.get('is_negative', False),
                    analysis_result.get('urgency_level', 'low'),
                    analysis_result.get('source', ''),
                    analysis_result.get('url', ''),
                    analysis_result.get('author', ''),
                    analysis_result.get('timestamp', datetime.now().isoformat()),
                    analysis_result.get('analysis_timestamp', datetime.now().isoformat()),
                    analysis_result.get('vader_score'),
                    analysis_result.get('textblob_score'),
                    analysis_result.get('transformer_score'),
                    json.dumps(analysis_result.get('metadata', {}))
                ))
                
                sentiment_id = cursor.lastrowid
                conn.commit()
                logger.debug(f"Inserted sentiment analysis with ID: {sentiment_id}")
                return sentiment_id
                
        except Exception as e:
            logger.error(f"Error inserting sentiment analysis: {e}")
            raise
    
    def create_alert(self, sentiment_id: int, alert_type: str, urgency_level: str, 
                    message: str, response_recommendation: str = None) -> int:
        """Create a new alert"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO alerts (
                        sentiment_id, alert_type, urgency_level, message,
                        response_recommendation
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (sentiment_id, alert_type, urgency_level, message, response_recommendation))
                
                alert_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Created alert {alert_id} for sentiment {sentiment_id}")
                return alert_id
                
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            raise
    
    def get_recent_negative_sentiment(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """Get recent negative sentiment analysis results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                query = '''
                    SELECT * FROM sentiment_analysis 
                    WHERE is_negative = TRUE 
                    AND timestamp >= ?
                    ORDER BY sentiment_score ASC, timestamp DESC
                    LIMIT ?
                '''
                
                df = pd.read_sql_query(query, conn, params=(cutoff_time, limit))
                return df.to_dict('records')
                
        except Exception as e:
            logger.error(f"Error getting recent negative sentiment: {e}")
            return []
    
    def get_active_alerts(self, urgency_level: str = None) -> List[Dict]:
        """Get active alerts, optionally filtered by urgency level"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if urgency_level:
                    query = '''
                        SELECT a.*, s.text, s.source, s.sentiment_score, s.urgency_level as sentiment_urgency
                        FROM alerts a
                        JOIN sentiment_analysis s ON a.sentiment_id = s.id
                        WHERE a.status = 'active' AND a.urgency_level = ?
                        ORDER BY a.created_at DESC
                    '''
                    df = pd.read_sql_query(query, conn, params=(urgency_level,))
                else:
                    query = '''
                        SELECT a.*, s.text, s.source, s.sentiment_score, s.urgency_level as sentiment_urgency
                        FROM alerts a
                        JOIN sentiment_analysis s ON a.sentiment_id = s.id
                        WHERE a.status = 'active'
                        ORDER BY a.created_at DESC
                    '''
                    df = pd.read_sql_query(query, conn)
                
                return df.to_dict('records')
                
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    def mark_alert_email_sent(self, alert_id: int):
        """Mark an alert as having email sent"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE alerts 
                    SET email_sent = TRUE, email_sent_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (alert_id,))
                conn.commit()
                logger.info(f"Marked alert {alert_id} as email sent")
                
        except Exception as e:
            logger.error(f"Error marking alert email sent: {e}")
    
    def log_email_send(self, alert_id: int, recipient_email: str, subject: str, 
                      body: str, status: str, error_message: str = None):
        """Log email sending attempt"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO email_logs (
                        alert_id, recipient_email, subject, body, status, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (alert_id, recipient_email, subject, body, status, error_message))
                conn.commit()
                logger.debug(f"Logged email send for alert {alert_id}")
                
        except Exception as e:
            logger.error(f"Error logging email send: {e}")
    
    def get_sentiment_statistics(self, days: int = 7) -> Dict:
        """Get sentiment statistics for the specified number of days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Overall sentiment distribution
                sentiment_query = '''
                    SELECT sentiment_category, COUNT(*) as count
                    FROM sentiment_analysis
                    WHERE timestamp >= ?
                    GROUP BY sentiment_category
                '''
                sentiment_df = pd.read_sql_query(sentiment_query, conn, params=(cutoff_time,))
                
                # Source distribution
                source_query = '''
                    SELECT source, COUNT(*) as count
                    FROM sentiment_analysis
                    WHERE timestamp >= ?
                    GROUP BY source
                '''
                source_df = pd.read_sql_query(source_query, conn, params=(cutoff_time,))
                
                # Urgency level distribution
                urgency_query = '''
                    SELECT urgency_level, COUNT(*) as count
                    FROM sentiment_analysis
                    WHERE timestamp >= ? AND is_negative = TRUE
                    GROUP BY urgency_level
                '''
                urgency_df = pd.read_sql_query(urgency_query, conn, params=(cutoff_time,))
                
                # Alert statistics
                alert_query = '''
                    SELECT COUNT(*) as total_alerts,
                           SUM(CASE WHEN email_sent = TRUE THEN 1 ELSE 0 END) as emails_sent
                    FROM alerts
                    WHERE created_at >= ?
                '''
                alert_df = pd.read_sql_query(alert_query, conn, params=(cutoff_time,))
                
                return {
                    'sentiment_distribution': sentiment_df.to_dict('records'),
                    'source_distribution': source_df.to_dict('records'),
                    'urgency_distribution': urgency_df.to_dict('records'),
                    'alert_statistics': alert_df.to_dict('records')[0] if not alert_df.empty else {},
                    'period_days': days
                }
                
        except Exception as e:
            logger.error(f"Error getting sentiment statistics: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old data to keep database size manageable"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Delete old sentiment analysis data
                cursor.execute('DELETE FROM sentiment_analysis WHERE timestamp < ?', (cutoff_time,))
                deleted_sentiment = cursor.rowcount
                
                # Delete old email logs
                cursor.execute('DELETE FROM email_logs WHERE sent_at < ?', (cutoff_time,))
                deleted_emails = cursor.rowcount
                
                conn.commit()
                logger.info(f"Cleaned up {deleted_sentiment} old sentiment records and {deleted_emails} email logs")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def close(self):
        """Close database connection"""
        # SQLite connections are automatically closed when they go out of scope
        pass
