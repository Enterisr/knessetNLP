"""
Sentiment analysis module.

This module handles sentiment analysis of translated text using TextBlob
and other sentiment analysis techniques.
"""

from .sentiment_analyzer import analyze_sentiment, SentimentAnalyzer

__all__ = ['analyze_sentiment', 'SentimentAnalyzer']
