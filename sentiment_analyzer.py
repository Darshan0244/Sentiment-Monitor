"""
Advanced sentiment analysis engine for customer feedback monitoring
"""
import re
import nltk
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from loguru import logger
import pandas as pd

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class SentimentAnalyzer:
    def __init__(self):
        """Initialize the sentiment analyzer with multiple models"""
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
        # Initialize transformer model for more accurate sentiment analysis
        try:
            # Try to import transformers and torch
            from transformers import pipeline
            import torch
            
            self.transformer_pipeline = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if torch.cuda.is_available() else -1
            )
            self.use_transformer = True
            logger.info("Transformer model loaded successfully")
        except ImportError:
            logger.info("Transformers not available, using VADER and TextBlob only")
            self.use_transformer = False
        except Exception as e:
            logger.warning(f"Could not load transformer model: {e}")
            self.use_transformer = False
        
        # Sentiment categories
        self.sentiment_categories = {
            'very_negative': -0.8,
            'negative': -0.3,
            'neutral': 0.1,
            'positive': 0.3,
            'very_positive': 0.8
        }
    
    def clean_text(self, text):
        """Clean and preprocess text for analysis"""
        if not text:
            return ""
        
        # Convert to string and lowercase
        text = str(text).lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\!\?]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def analyze_sentiment_vader(self, text):
        """Analyze sentiment using VADER"""
        cleaned_text = self.clean_text(text)
        scores = self.vader_analyzer.polarity_scores(cleaned_text)
        
        return {
            'compound': scores['compound'],
            'positive': scores['pos'],
            'negative': scores['neg'],
            'neutral': scores['neu']
        }
    
    def analyze_sentiment_textblob(self, text):
        """Analyze sentiment using TextBlob"""
        cleaned_text = self.clean_text(text)
        blob = TextBlob(cleaned_text)
        
        return {
            'polarity': blob.sentiment.polarity,
            'subjectivity': blob.sentiment.subjectivity
        }
    
    def analyze_sentiment_transformer(self, text):
        """Analyze sentiment using transformer model"""
        if not self.use_transformer:
            return None
        
        try:
            cleaned_text = self.clean_text(text)
            if len(cleaned_text) > 512:  # Truncate if too long
                cleaned_text = cleaned_text[:512]
            
            result = self.transformer_pipeline(cleaned_text)[0]
            
            # Map transformer labels to numerical scores
            label_mapping = {
                'LABEL_0': -0.8,  # Negative
                'LABEL_1': 0.0,   # Neutral
                'LABEL_2': 0.8    # Positive
            }
            
            return {
                'label': result['label'],
                'score': result['score'],
                'polarity': label_mapping.get(result['label'], 0.0)
            }
        except Exception as e:
            logger.error(f"Transformer analysis failed: {e}")
            return None
    
    def get_sentiment_category(self, score):
        """Categorize sentiment score"""
        if score <= self.sentiment_categories['very_negative']:
            return 'very_negative'
        elif score <= self.sentiment_categories['negative']:
            return 'negative'
        elif score <= self.sentiment_categories['neutral']:
            return 'neutral'
        elif score <= self.sentiment_categories['positive']:
            return 'positive'
        else:
            return 'very_positive'
    
    def analyze_sentiment(self, text, source=None):
        """
        Comprehensive sentiment analysis using multiple models
        Returns a detailed sentiment analysis result
        """
        if not text or not text.strip():
            return {
                'text': text,
                'sentiment_score': 0.0,
                'sentiment_category': 'neutral',
                'confidence': 0.0,
                'is_negative': False,
                'urgency_level': 'low',
                'source': source
            }
        
        # Get sentiment scores from different models
        vader_result = self.analyze_sentiment_vader(text)
        textblob_result = self.analyze_sentiment_textblob(text)
        transformer_result = self.analyze_sentiment_transformer(text)
        
        # Calculate weighted average sentiment score
        scores = []
        weights = []
        
        # VADER (good for social media)
        scores.append(vader_result['compound'])
        weights.append(0.3)
        
        # TextBlob (good for general text)
        scores.append(textblob_result['polarity'])
        weights.append(0.3)
        
        # Transformer (most accurate)
        if transformer_result:
            scores.append(transformer_result['polarity'])
            weights.append(0.4)
        else:
            # Redistribute weights if transformer fails
            weights = [0.5, 0.5]
        
        # Calculate weighted average
        final_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        
        # Determine sentiment category
        sentiment_category = self.get_sentiment_category(final_score)
        
        # Calculate confidence based on agreement between models
        score_variance = sum((s - final_score) ** 2 for s in scores) / len(scores)
        confidence = max(0.0, 1.0 - score_variance)
        
        # Determine if negative and urgency level
        is_negative = final_score < -0.1
        urgency_level = self._calculate_urgency_level(final_score, text, confidence)
        
        result = {
            'text': text,
            'sentiment_score': round(final_score, 3),
            'sentiment_category': sentiment_category,
            'confidence': round(confidence, 3),
            'is_negative': is_negative,
            'urgency_level': urgency_level,
            'source': source,
            'vader_score': vader_result['compound'],
            'textblob_score': textblob_result['polarity'],
            'transformer_score': transformer_result['polarity'] if transformer_result else None,
            'analysis_timestamp': pd.Timestamp.now().isoformat()
        }
        
        logger.info(f"Sentiment analysis: {sentiment_category} ({final_score:.3f}) - {text[:50]}...")
        
        return result
    
    def _calculate_urgency_level(self, score, text, confidence):
        """Calculate urgency level based on sentiment and content"""
        urgency_keywords = [
            'urgent', 'emergency', 'immediately', 'asap', 'critical',
            'terrible', 'awful', 'horrible', 'worst', 'hate', 'sue',
            'legal', 'lawyer', 'complaint', 'refund', 'cancel'
        ]
        
        text_lower = text.lower()
        has_urgency_keywords = any(keyword in text_lower for keyword in urgency_keywords)
        
        if score < -0.7 and confidence > 0.8:
            return 'critical'
        elif score < -0.5 and (confidence > 0.7 or has_urgency_keywords):
            return 'high'
        elif score < -0.2:
            return 'medium'
        else:
            return 'low'
    
    def batch_analyze(self, texts, sources=None):
        """Analyze multiple texts in batch"""
        if sources is None:
            sources = [None] * len(texts)
        
        results = []
        for text, source in zip(texts, sources):
            result = self.analyze_sentiment(text, source)
            results.append(result)
        
        return results
