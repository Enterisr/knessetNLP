"""
Core analysis modules for Knesset NLP processing.

This package contains the main analysis components:
- embedder: Text embedding functionality
- sentiment_analyzer: Sentiment analysis using translation and TextBlob  
- translator: Hebrew to English translation
"""

from .embedder import embed
from .sentiment_analyzer import analyze_sentiment
from .translator import HebToEngTranslator

__all__ = ['embed', 'analyze_sentiment', 'HebToEngTranslator']
