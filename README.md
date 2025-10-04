# Customer Sentiment Alert System

A comprehensive real-time monitoring system that tracks customer sentiment across reviews, social media, and forums, providing instant alerts to support teams when negative sentiment is detected.

## 🚀 Features

- **Real-time Sentiment Analysis**: Advanced NLP using multiple models (VADER, TextBlob, Transformer)
- **Multi-source Monitoring**: Reviews (Trustpilot, Yelp, Google), Social Media (Twitter, Reddit), Forums (Stack Overflow, Quora)
- **Intelligent Alerting**: Urgency-based alerts with response recommendations
- **Email Notifications**: Beautiful HTML email templates with actionable insights
- **Web Dashboard**: Real-time monitoring dashboard with statistics and alerts
- **Configurable Monitoring**: Customizable keywords, companies, and thresholds
- **Data Persistence**: SQLite database with comprehensive logging

## 📋 Requirements

- Python 3.8+
- Chrome/Chromium browser (for web scraping)
- Email account for SMTP (Gmail recommended)
- Optional: Twitter API credentials for enhanced social media monitoring

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd customer-sentiment-alert-system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install ChromeDriver**
   - Download ChromeDriver from [ChromeDriver Downloads](https://chromedriver.chromium.org/)
   - Add to your system PATH or place in the project directory

4. **Configure environment variables**
   ```bash
   cp env_example.txt .env
   ```
   Edit `.env` with your configuration:
   ```env
   EMAIL_USERNAME=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   ALERT_EMAIL=support@yourcompany.com
   TWITTER_API_KEY=your_twitter_api_key
   # ... other variables
   ```

5. **Update configuration**
   Edit `config.py` to add your company names and monitoring keywords:
   ```python
   COMPANY_NAMES = [
       'YourCompany',
       'YourBrand',
       'YourProduct'
   ]
   
   MONITOR_KEYWORDS = [
       'customer service', 'support', 'complaint', 'issue', 'problem',
       'refund', 'cancel', 'dissatisfied', 'terrible', 'awful'
   ]
   ```

## 🚀 Usage

### Start the Web Dashboard
```bash
python app.py
```
Access the dashboard at `http://localhost:5000`

### Start Monitoring
```bash
python sentiment_monitor.py
```

### Run Both Together
```bash
# Terminal 1: Start the dashboard
python app.py

# Terminal 2: Start monitoring
python sentiment_monitor.py
```

## 📊 Dashboard Features

### Main Dashboard
- Real-time sentiment statistics
- Active alerts overview
- Recent negative sentiment
- Interactive charts and visualizations

### Alerts Management
- Filter alerts by urgency level
- View detailed customer feedback
- Response recommendations
- Email status tracking

### Statistics
- Sentiment distribution charts
- Source analysis
- Urgency level breakdown
- Historical trends

### Configuration
- System status monitoring
- Quick action buttons
- Environment variable status
- Log file management

## 🔧 Configuration

### Email Setup (Gmail)
1. Enable 2-factor authentication
2. Generate an App Password
3. Use the App Password in `EMAIL_PASSWORD`

### Twitter API Setup (Optional)
1. Create a Twitter Developer account
2. Create a new app
3. Generate API keys and tokens
4. Add to environment variables

### Monitoring Configuration
- `MONITORING_INTERVAL`: How often to check for new mentions (seconds)
- `SENTIMENT_THRESHOLD`: Negative sentiment threshold (-1.0 to 1.0)
- `COMPANY_NAMES`: List of company/brand names to monitor
- `MONITOR_KEYWORDS`: Keywords that trigger monitoring

## 📧 Email Templates

The system includes beautiful HTML email templates for:
- **Critical Alerts**: Immediate attention required
- **High Priority Alerts**: Important negative sentiment
- **Medium Priority Alerts**: Standard negative sentiment
- **Daily Summary**: Overview of daily activity

## 🗄️ Database Schema

The system uses SQLite with the following tables:
- `sentiment_analysis`: Stores all sentiment analysis results
- `alerts`: Manages alert creation and status
- `email_logs`: Tracks email sending attempts
- `monitoring_config`: Stores monitoring configuration

## 🔍 Monitoring Sources

### Review Sites
- **Trustpilot**: Company reviews and ratings
- **Yelp**: Business reviews and feedback
- **Google Reviews**: Google Maps business reviews

### Social Media
- **Twitter**: Mentions and hashtags (requires API)
- **Reddit**: Posts and comments mentioning your brand

### Forums
- **Stack Overflow**: Technical discussions
- **Quora**: Q&A platform mentions

## 🚨 Alert System

### Urgency Levels
- **Critical**: Sentiment score < -0.7, high confidence
- **High**: Sentiment score < -0.5, medium confidence
- **Medium**: Sentiment score < -0.2
- **Low**: Other negative sentiment

### Response Recommendations
The system automatically generates response recommendations based on:
- Sentiment severity
- Source platform
- Content keywords
- Historical patterns

## 🛡️ Security Considerations

- Store sensitive credentials in environment variables
- Use App Passwords for email accounts
- Regularly rotate API keys
- Monitor log files for suspicious activity
- Use HTTPS in production

## 📈 Performance Optimization

- Adjust monitoring intervals based on your needs
- Use database cleanup to manage storage
- Monitor system resources during peak usage
- Consider using a dedicated server for production

## 🐛 Troubleshooting

### Common Issues

1. **ChromeDriver not found**
   - Download ChromeDriver and add to PATH
   - Ensure Chrome browser is installed

2. **Email not sending**
   - Check SMTP credentials
   - Verify App Password for Gmail
   - Check firewall settings

3. **Twitter API errors**
   - Verify API credentials
   - Check rate limits
   - Ensure proper permissions

4. **Database errors**
   - Check file permissions
   - Verify disk space
   - Review log files

### Log Files
Check `sentiment_alerts.log` for detailed error information and system status.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Review log files for errors
- Create an issue in the repository
- Contact the development team

## 🔮 Future Enhancements

- Machine learning model training on historical data
- Integration with CRM systems
- Advanced analytics and reporting
- Mobile app for alerts
- Integration with more social platforms
- Automated response suggestions
- Sentiment trend analysis
- Competitive monitoring

---

**Built with ❤️ for customer support teams**
