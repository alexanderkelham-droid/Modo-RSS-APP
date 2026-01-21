"""
Country tagging service for articles.
"""

import re
from typing import List, Tuple, Dict, Optional
from collections import Counter

from app.services.nlp.country_data import (
    COUNTRY_KEYWORDS,
    REGION_KEYWORDS,
    AMBIGUOUS_KEYWORDS,
)


class CountryTagger:
    """
    Tags articles with country codes using keyword matching.
    """
    
    def __init__(self, max_countries: int = 3):
        """
        Initialize country tagger.
        
        Args:
            max_countries: Maximum number of country tags to return
        """
        self.max_countries = max_countries
        self._build_keyword_index()
    
    def _build_keyword_index(self):
        """Build reverse index: keyword -> country code."""
        self.keyword_to_country: Dict[str, str] = {}
        
        for code, keywords in COUNTRY_KEYWORDS.items():
            for keyword in keywords:
                self.keyword_to_country[keyword.lower()] = code
        
        # Build region keyword index
        self.keyword_to_region: Dict[str, str] = {}
        for region, keywords in REGION_KEYWORDS.items():
            for keyword in keywords:
                self.keyword_to_region[keyword.lower()] = region
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words and multi-word phrases.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens (words and phrases)
        """
        if not text:
            return []
        
        # Lowercase
        text = text.lower()
        
        # Generate n-grams (1-5 words)
        tokens = []
        words = re.findall(r'\b\w+\b|[.,!?;]', text)
        
        # Add individual words
        tokens.extend(words)
        
        # Add bigrams (2-word phrases)
        for i in range(len(words) - 1):
            tokens.append(f"{words[i]} {words[i+1]}")
        
        # Add trigrams (3-word phrases)
        for i in range(len(words) - 2):
            tokens.append(f"{words[i]} {words[i+1]} {words[i+2]}")
        
        # Add 4-grams
        for i in range(len(words) - 3):
            tokens.append(f"{words[i]} {words[i+1]} {words[i+2]} {words[i+3]}")
        
        # Add 5-grams (for "people's republic of china", etc.)
        for i in range(len(words) - 4):
            tokens.append(f"{words[i]} {words[i+1]} {words[i+2]} {words[i+3]} {words[i+4]}")
        
        return tokens
    
    def _handle_ambiguous_terms(
        self,
        text: str,
        country_scores: Counter,
    ) -> Counter:
        """
        Handle ambiguous terms like "Georgia" (US state vs. country).
        
        Args:
            text: Full text for context
            country_scores: Current country scores
            
        Returns:
            Updated country scores
        """
        text_lower = text.lower()
        
        # Georgia: if "georgia" appears with US context, remove GE
        if "GE" in country_scores:
            # Check for US state indicators
            us_indicators = ["atlanta", "savannah", "peach state", "georgian state"]
            if any(indicator in text_lower for indicator in us_indicators):
                # This is likely Georgia (US state), not Georgia (country)
                country_scores["GE"] = 0
        
        return country_scores
    
    def _score_countries(
        self,
        tokens: List[str],
        title_tokens: List[str],
    ) -> Tuple[Counter, Dict[str, List[str]]]:
        """
        Score countries based on keyword matches.
        
        Args:
            tokens: Tokens from full text
            title_tokens: Tokens from title
            
        Returns:
            Tuple of (country_scores, region_metadata)
        """
        country_scores = Counter()
        regions_found = {}
        
        # Score countries
        for token in tokens:
            if token in self.keyword_to_country:
                code = self.keyword_to_country[token]
                
                # Title matches get higher weight
                weight = 3 if token in title_tokens else 1
                
                # Longer phrases get higher weight (more specific)
                phrase_length = len(token.split())
                weight *= phrase_length
                
                country_scores[code] += weight
        
        # Detect regions (EU, etc.) but don't add to country list
        for token in tokens:
            if token in self.keyword_to_region:
                region = self.keyword_to_region[token]
                if region not in regions_found:
                    regions_found[region] = []
                regions_found[region].append(token)
        
        return country_scores, regions_found
    
    def tag_article(
        self,
        title: str,
        content: Optional[str] = None,
    ) -> Tuple[List[str], Dict]:
        """
        Tag article with country codes and metadata.
        
        Args:
            title: Article title
            content: Article content text (optional)
            
        Returns:
            Tuple of (country_codes, metadata)
            - country_codes: List of ISO alpha-2 codes (max 3)
            - metadata: Dict with regions and other info
        """
        # Combine title and content
        full_text = title
        if content:
            full_text += " " + content
        
        if not full_text.strip():
            return [], {}
        
        # Tokenize
        title_tokens = set(self._tokenize(title))
        full_tokens = self._tokenize(full_text)
        
        # Score countries
        country_scores, regions_found = self._score_countries(full_tokens, title_tokens)
        
        # Handle ambiguous terms
        country_scores = self._handle_ambiguous_terms(full_text, country_scores)
        
        # Get top N countries
        top_countries = [
            code for code, score in country_scores.most_common(self.max_countries)
            if score > 0
        ]
        
        # Build metadata
        metadata = {}
        if regions_found:
            metadata["regions"] = list(regions_found.keys())
        
        return top_countries, metadata
    
    def tag_text(self, text: str) -> List[str]:
        """
        Simple convenience method to tag text without metadata.
        
        Args:
            text: Text to tag
            
        Returns:
            List of ISO alpha-2 country codes
        """
        countries, _ = self.tag_article(text, None)
        return countries
