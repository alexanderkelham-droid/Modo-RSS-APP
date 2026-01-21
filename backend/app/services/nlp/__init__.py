"""
NLP services for language detection, country tagging, and topic classification.
"""

from app.services.nlp.country_tagger import CountryTagger
from app.services.nlp.topic_tagger import TopicTagger

__all__ = [
    "CountryTagger",
    "TopicTagger",
]
