"""
Filter database package for handling filtered utterance storage and reporting.
"""

# Import classes to make them available at package level
try:
    from .report_generator import FilterReportGenerator
    from .storage import FilteredUtteranceStorage

    __all__ = ['FilterReportGenerator', 'FilteredUtteranceStorage']
except ImportError:
    # Graceful fallback if modules aren't found
    __all__ = []
