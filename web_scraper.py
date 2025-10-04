"""
Web scraping module for monitoring reviews, social media, and forums
"""
import requests
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import tweepy
from loguru import logger
from datetime import datetime, timedelta
import json
from urllib.parse import urljoin, urlparse
import random

class WebScraper:
    def __init__(self, config):
        """Initialize web scraper with configuration"""
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Initialize Selenium driver
        self.driver = None
        self._setup_selenium()
        
        # Initialize Twitter API if credentials are available
        self.twitter_api = None
        self._setup_twitter_api()
    
    def _setup_selenium(self):
        """Setup Selenium WebDriver with Chrome options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium WebDriver: {e}")
            self.driver = None
    
    def _setup_twitter_api(self):
        """Setup Twitter API client"""
        try:
            if all([self.config.TWITTER_API_KEY, self.config.TWITTER_API_SECRET,
                   self.config.TWITTER_ACCESS_TOKEN, self.config.TWITTER_ACCESS_TOKEN_SECRET]):
                
                auth = tweepy.OAuthHandler(
                    self.config.TWITTER_API_KEY,
                    self.config.TWITTER_API_SECRET
                )
                auth.set_access_token(
                    self.config.TWITTER_ACCESS_TOKEN,
                    self.config.TWITTER_ACCESS_TOKEN_SECRET
                )
                
                self.twitter_api = tweepy.API(auth, wait_on_rate_limit=True)
                logger.info("Twitter API initialized successfully")
            else:
                logger.warning("Twitter API credentials not provided")
        except Exception as e:
            logger.error(f"Failed to initialize Twitter API: {e}")
    
    def scrape_review_sites(self, company_name, keywords=None):
        """Scrape review sites for mentions of the company"""
        if keywords is None:
            keywords = self.config.MONITOR_KEYWORDS
        
        all_reviews = []
        
        # Scrape Trustpilot
        trustpilot_reviews = self._scrape_trustpilot(company_name, keywords)
        all_reviews.extend(trustpilot_reviews)
        
        # Scrape Yelp
        yelp_reviews = self._scrape_yelp(company_name, keywords)
        all_reviews.extend(yelp_reviews)
        
        # Scrape Google Reviews
        google_reviews = self._scrape_google_reviews(company_name, keywords)
        all_reviews.extend(google_reviews)
        
        return all_reviews
    
    def _scrape_trustpilot(self, company_name, keywords):
        """Scrape Trustpilot reviews"""
        reviews = []
        try:
            # Search for company on Trustpilot
            search_url = f"https://www.trustpilot.com/search?query={company_name}"
            
            if self.driver:
                self.driver.get(search_url)
                time.sleep(3)
                
                # Find company profile link
                try:
                    company_link = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-review-count]"))
                    )
                    company_url = company_link.get_attribute('href')
                    
                    # Navigate to company reviews
                    self.driver.get(company_url)
                    time.sleep(3)
                    
                    # Extract reviews
                    review_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-review-id]")
                    
                    for element in review_elements[:10]:  # Limit to 10 reviews
                        try:
                            review_text = element.find_element(By.CSS_SELECTOR, ".review-content__text").text
                            rating_element = element.find_element(By.CSS_SELECTOR, "[data-star-rating]")
                            rating = rating_element.get_attribute('data-star-rating')
                            
                            if self._contains_keywords(review_text, keywords):
                                reviews.append({
                                    'source': 'Trustpilot',
                                    'text': review_text,
                                    'rating': rating,
                                    'url': company_url,
                                    'timestamp': datetime.now().isoformat()
                                })
                        except NoSuchElementException:
                            continue
                            
                except TimeoutException:
                    logger.warning("Could not find company on Trustpilot")
                    
        except Exception as e:
            logger.error(f"Error scraping Trustpilot: {e}")
        
        return reviews
    
    def _scrape_yelp(self, company_name, keywords):
        """Scrape Yelp reviews"""
        reviews = []
        try:
            search_url = f"https://www.yelp.com/search?find_desc={company_name}"
            
            if self.driver:
                self.driver.get(search_url)
                time.sleep(3)
                
                # Find business link
                try:
                    business_link = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-testid='business-name']"))
                    )
                    business_url = business_link.get_attribute('href')
                    
                    # Navigate to business reviews
                    self.driver.get(business_url)
                    time.sleep(3)
                    
                    # Extract reviews
                    review_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-review-id]")
                    
                    for element in review_elements[:10]:
                        try:
                            review_text = element.find_element(By.CSS_SELECTOR, ".comment__09f24__D0cxf").text
                            rating_element = element.find_element(By.CSS_SELECTOR, "[role='img']")
                            rating = rating_element.get_attribute('aria-label')
                            
                            if self._contains_keywords(review_text, keywords):
                                reviews.append({
                                    'source': 'Yelp',
                                    'text': review_text,
                                    'rating': rating,
                                    'url': business_url,
                                    'timestamp': datetime.now().isoformat()
                                })
                        except NoSuchElementException:
                            continue
                            
                except TimeoutException:
                    logger.warning("Could not find company on Yelp")
                    
        except Exception as e:
            logger.error(f"Error scraping Yelp: {e}")
        
        return reviews
    
    def _scrape_google_reviews(self, company_name, keywords):
        """Scrape Google Reviews"""
        reviews = []
        try:
            search_url = f"https://www.google.com/search?q={company_name}+reviews"
            
            if self.driver:
                self.driver.get(search_url)
                time.sleep(3)
                
                # Look for review snippets
                review_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-ved]")
                
                for element in review_elements[:5]:
                    try:
                        review_text = element.text
                        if review_text and len(review_text) > 20:
                            if self._contains_keywords(review_text, keywords):
                                reviews.append({
                                    'source': 'Google',
                                    'text': review_text,
                                    'rating': None,
                                    'url': search_url,
                                    'timestamp': datetime.now().isoformat()
                                })
                    except Exception:
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping Google Reviews: {e}")
        
        return reviews
    
    def scrape_social_media(self, company_name, keywords=None):
        """Scrape social media platforms for mentions"""
        if keywords is None:
            keywords = self.config.MONITOR_KEYWORDS
        
        all_mentions = []
        
        # Scrape Twitter
        twitter_mentions = self._scrape_twitter(company_name, keywords)
        all_mentions.extend(twitter_mentions)
        
        # Scrape Reddit
        reddit_mentions = self._scrape_reddit(company_name, keywords)
        all_mentions.extend(reddit_mentions)
        
        return all_mentions
    
    def _scrape_twitter(self, company_name, keywords):
        """Scrape Twitter for mentions"""
        mentions = []
        
        if not self.twitter_api:
            logger.warning("Twitter API not available")
            return mentions
        
        try:
            # Search for tweets mentioning the company
            search_query = f"{company_name} -is:retweet"
            
            tweets = tweepy.Cursor(
                self.twitter_api.search_tweets,
                q=search_query,
                lang='en',
                result_type='recent',
                count=100
            ).items(50)
            
            for tweet in tweets:
                tweet_text = tweet.text
                if self._contains_keywords(tweet_text, keywords):
                    mentions.append({
                        'source': 'Twitter',
                        'text': tweet_text,
                        'author': tweet.user.screen_name,
                        'url': f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}",
                        'timestamp': tweet.created_at.isoformat(),
                        'retweet_count': tweet.retweet_count,
                        'favorite_count': tweet.favorite_count
                    })
                    
        except Exception as e:
            logger.error(f"Error scraping Twitter: {e}")
        
        return mentions
    
    def _scrape_reddit(self, company_name, keywords):
        """Scrape Reddit for mentions"""
        mentions = []
        try:
            # Use Reddit's JSON API
            search_url = f"https://www.reddit.com/search.json?q={company_name}&sort=new&limit=25"
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                for post in data.get('data', {}).get('children', []):
                    post_data = post.get('data', {})
                    title = post_data.get('title', '')
                    selftext = post_data.get('selftext', '')
                    full_text = f"{title} {selftext}"
                    
                    if self._contains_keywords(full_text, keywords):
                        mentions.append({
                            'source': 'Reddit',
                            'text': full_text,
                            'title': title,
                            'author': post_data.get('author', ''),
                            'url': f"https://reddit.com{post_data.get('permalink', '')}",
                            'timestamp': datetime.fromtimestamp(post_data.get('created_utc', 0)).isoformat(),
                            'score': post_data.get('score', 0),
                            'subreddit': post_data.get('subreddit', '')
                        })
                        
        except Exception as e:
            logger.error(f"Error scraping Reddit: {e}")
        
        return mentions
    
    def scrape_forums(self, company_name, keywords=None):
        """Scrape various forums for mentions"""
        if keywords is None:
            keywords = self.config.MONITOR_KEYWORDS
        
        all_posts = []
        
        # Scrape Stack Overflow
        stackoverflow_posts = self._scrape_stackoverflow(company_name, keywords)
        all_posts.extend(stackoverflow_posts)
        
        # Scrape Quora
        quora_posts = self._scrape_quora(company_name, keywords)
        all_posts.extend(quora_posts)
        
        return all_posts
    
    def _scrape_stackoverflow(self, company_name, keywords):
        """Scrape Stack Overflow for mentions"""
        posts = []
        try:
            search_url = f"https://stackoverflow.com/search?q={company_name}"
            
            if self.driver:
                self.driver.get(search_url)
                time.sleep(3)
                
                # Extract question titles and excerpts
                question_elements = self.driver.find_elements(By.CSS_SELECTOR, ".question-summary")
                
                for element in question_elements[:10]:
                    try:
                        title_element = element.find_element(By.CSS_SELECTOR, ".question-hyperlink")
                        title = title_element.text
                        excerpt_element = element.find_element(By.CSS_SELECTOR, ".excerpt")
                        excerpt = excerpt_element.text
                        full_text = f"{title} {excerpt}"
                        
                        if self._contains_keywords(full_text, keywords):
                            posts.append({
                                'source': 'Stack Overflow',
                                'text': full_text,
                                'title': title,
                                'url': title_element.get_attribute('href'),
                                'timestamp': datetime.now().isoformat()
                            })
                    except NoSuchElementException:
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping Stack Overflow: {e}")
        
        return posts
    
    def _scrape_quora(self, company_name, keywords):
        """Scrape Quora for mentions"""
        posts = []
        try:
            search_url = f"https://www.quora.com/search?q={company_name}"
            
            if self.driver:
                self.driver.get(search_url)
                time.sleep(3)
                
                # Extract question titles
                question_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='question-title']")
                
                for element in question_elements[:10]:
                    try:
                        title = element.text
                        if self._contains_keywords(title, keywords):
                            posts.append({
                                'source': 'Quora',
                                'text': title,
                                'title': title,
                                'url': element.get_attribute('href'),
                                'timestamp': datetime.now().isoformat()
                            })
                    except Exception:
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping Quora: {e}")
        
        return posts
    
    def _contains_keywords(self, text, keywords):
        """Check if text contains any of the monitoring keywords"""
        if not text or not keywords:
            return True
        
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def scrape_all_sources(self, company_names=None):
        """Scrape all configured sources for all company names"""
        if company_names is None:
            company_names = self.config.COMPANY_NAMES
        
        all_data = []
        
        for company_name in company_names:
            logger.info(f"Scraping data for {company_name}")
            
            # Scrape reviews
            reviews = self.scrape_review_sites(company_name)
            all_data.extend(reviews)
            
            # Scrape social media
            social_mentions = self.scrape_social_media(company_name)
            all_data.extend(social_mentions)
            
            # Scrape forums
            forum_posts = self.scrape_forums(company_name)
            all_data.extend(forum_posts)
            
            # Add delay between companies to avoid rate limiting
            time.sleep(2)
        
        logger.info(f"Scraped {len(all_data)} total mentions")
        return all_data
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            logger.info("Selenium WebDriver closed")
