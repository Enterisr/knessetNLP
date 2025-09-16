"""
Translation module for Hebrew to English translation.

This module handles the translation pipeline step, converting Hebrew text
to English using LibreTranslate or Google Translate as fallback.
"""

from .heb_to_eng_translator import HebToEngTranslator

__all__ = ['HebToEngTranslator']
