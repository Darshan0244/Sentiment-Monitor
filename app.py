"""
Flask web application for the Customer Sentiment Alert System dashboard
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
import json
import sqlite3
from datetime import datetime, timedelta
from loguru import logger

from config import Config
from sentiment_monitor import get_monitor, SentimentMonitor
from database import SentimentDatabase

app = Flask(__name__)
app.config['SECRET_KEY'] = Config().SECRET_KEY
CORS(app)

# Custom Jinja2 filters
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    """Convert datetime string to formatted string"""
    if not value:
        return 'Unknown'
    try:
        if isinstance(value, str):
            # Try to parse ISO format first
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                # Fallback to other common formats
                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        else:
            dt = value
        return dt.strftime(format)
    except:
        return str(value)

app.jinja_env.filters['datetimeformat'] = datetimeformat

# Initialize components
config = Config()
monitor = get_monitor()
database = SentimentDatabase()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        # Get recent statistics
        stats = database.get_sentiment_statistics(days=7)
        
        # Get active alerts
        active_alerts = database.get_active_alerts()
        
        # Get recent negative sentiment
        recent_negative = database.get_recent_negative_sentiment(hours=24, limit=10)
        
        return render_template('dashboard.html', 
                             stats=stats,
                             active_alerts=active_alerts,
                             recent_negative=recent_negative)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        # Don't flash error message to avoid persistent errors
        return render_template('dashboard.html', 
                             stats={
                                 'sentiment_distribution': [],
                                 'source_distribution': [],
                                 'urgency_distribution': [],
                                 'alert_statistics': {}
                             },
                             active_alerts=[],
                             recent_negative=[])

@app.route('/alerts')
def alerts():
    """Alerts page"""
    try:
        urgency_filter = request.args.get('urgency', '')
        alerts_data = database.get_active_alerts(urgency_filter if urgency_filter else None)
        
        return render_template('alerts.html', alerts=alerts_data, urgency_filter=urgency_filter)
    except Exception as e:
        logger.error(f"Error loading alerts: {e}")
        # Don't flash error message to avoid persistent errors
        return render_template('alerts.html', alerts=[])

@app.route('/statistics')
def statistics():
    """Statistics page"""
    try:
        days = int(request.args.get('days', 7))
        stats = database.get_sentiment_statistics(days=days)
        
        return render_template('statistics.html', stats=stats, days=days)
    except Exception as e:
        logger.error(f"Error loading statistics: {e}")
        # Don't flash error message to avoid persistent errors
        return render_template('statistics.html', 
                             stats={
                                 'sentiment_distribution': [],
                                 'source_distribution': [],
                                 'urgency_distribution': [],
                                 'alert_statistics': {}
                             }, 
                             days=7)

@app.route('/configuration')
def configuration():
    """Configuration page"""
    try:
        return render_template('configuration.html', config=config)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        flash('Error loading configuration', 'error')
        return render_template('configuration.html', config=config)

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    try:
        days = int(request.args.get('days', 7))
        stats = database.get_sentiment_statistics(days=days)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts')
def api_alerts():
    """API endpoint for alerts"""
    try:
        urgency = request.args.get('urgency')
        alerts = database.get_active_alerts(urgency)
        return jsonify(alerts)
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent-negative')
def api_recent_negative():
    """API endpoint for recent negative sentiment"""
    try:
        hours = int(request.args.get('hours', 24))
        limit = int(request.args.get('limit', 10))
        data = database.get_recent_negative_sentiment(hours=hours, limit=limit)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting recent negative sentiment: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-system')
def api_test_system():
    """API endpoint for system testing"""
    try:
        test_results = monitor.test_system()
        return jsonify(test_results)
    except Exception as e:
        logger.error(f"Error testing system: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/manual-scan', methods=['POST'])
def api_manual_scan():
    """API endpoint for manual scanning"""
    try:
        data = request.get_json()
        company_name = data.get('company_name') if data else None
        
        # Add CORS headers for the response
        response = jsonify({
            'success': True,
            'companies_scanned': [company_name] if company_name else ['YourCompany', 'YourBrand', 'YourProduct'],
            'items_found': 0,
            'items_analyzed': 0,
            'negative_items': 0,
            'message': 'Manual scan completed. Note: Web scraping is disabled in demo mode.'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    except Exception as e:
        logger.error(f"Error during manual scan: {e}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/api/start-monitoring', methods=['POST'])
def api_start_monitoring():
    """API endpoint to start monitoring"""
    try:
        monitor.start_monitoring()
        return jsonify({'success': True, 'message': 'Monitoring started'})
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop-monitoring', methods=['POST'])
def api_stop_monitoring():
    """API endpoint to stop monitoring"""
    try:
        monitor.stop_monitoring()
        return jsonify({'success': True, 'message': 'Monitoring stopped'})
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-test-email', methods=['POST'])
def api_send_test_email():
    """API endpoint to send test email"""
    try:
        # Create a test alert
        test_sentiment_data = {
            'text': 'This is a test message to verify email functionality.',
            'source': 'Test System',
            'sentiment_score': -0.5,
            'confidence': 0.8,
            'timestamp': datetime.now().isoformat(),
            'url': 'https://example.com'
        }
        
        test_alert_data = {
            'id': 999,
            'urgency_level': 'medium',
            'response_recommendation': 'This is a test email. Please ignore.'
        }
        
        success = monitor.email_notifier.send_alert_email(test_alert_data, test_sentiment_data)
        
        if success:
            return jsonify({'success': True, 'message': 'Test email sent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send test email'})
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alert-details/<int:alert_id>')
def api_alert_details(alert_id):
    """API endpoint to get detailed alert information"""
    try:
        with sqlite3.connect(database.db_path) as conn:
            cursor = conn.cursor()
            query = '''
                SELECT a.*, s.text, s.source, s.sentiment_score, s.urgency_level as sentiment_urgency, s.source_url
                FROM alerts a
                JOIN sentiment_analysis s ON a.sentiment_id = s.id
                WHERE a.id = ?
            '''
            cursor.execute(query, (alert_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [description[0] for description in cursor.description]
                alert_data = dict(zip(columns, row))
                return jsonify(alert_data)
            else:
                return jsonify({'error': 'Alert not found'}), 404
                
    except Exception as e:
        logger.error(f"Error getting alert details: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/resolve-alert/<int:alert_id>', methods=['POST'])
def api_resolve_alert(alert_id):
    """API endpoint to mark an alert as resolved"""
    try:
        with sqlite3.connect(database.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE alerts SET status = "resolved" WHERE id = ?',
                (alert_id,)
            )
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Alert {alert_id} marked as resolved")
                return jsonify({'success': True, 'message': 'Alert resolved successfully'})
            else:
                return jsonify({'error': 'Alert not found'}), 404
                
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def api_logs():
    """API endpoint to get recent log entries"""
    try:
        import os
        log_file = config.LOG_FILE
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Get last 50 lines
                recent_lines = lines[-50:] if len(lines) > 50 else lines
                # Clean up log format
                clean_lines = [line.strip() for line in recent_lines if line.strip()]
                return jsonify({'logs': clean_lines})
        else:
            return jsonify({'logs': ['No log file found']})
            
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    import os
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(debug=config.DEBUG, host='0.0.0.0', port=5000)
