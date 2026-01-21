"""
RSS feed parsing utilities.
"""

import feedparser
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from email.utils import parsedate_to_datetime


class RSSEntry:
    """Parsed RSS entry data."""
    
    def __init__(
        self,
        title: str,
        url: str,
        published_at: Optional[datetime] = None,
        summary: Optional[str] = None,
    ):
        self.title = title
        self.url = url
        self.published_at = published_at
        self.summary = summary
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at,
            "summary": self.summary,
        }
    
    def __repr__(self):
        return f"<RSSEntry(title='{self.title[:50]}...', url='{self.url}')>"


class RSSParser:
    """Parser for RSS feeds using feedparser."""
    
    @staticmethod
    def parse_published_date(entry: Dict) -> Optional[datetime]:
        """
        Extract and parse published date from RSS entry.
        Tries multiple common fields: published, pubDate, updated.
        """
        date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
        
        for field in date_fields:
            if hasattr(entry, field):
                time_struct = getattr(entry, field)
                if time_struct:
                    try:
                        return datetime(*time_struct[:6])
                    except (TypeError, ValueError):
                        pass
        
        # Try string parsing as fallback
        string_fields = ['published', 'pubDate', 'updated']
        for field in string_fields:
            if hasattr(entry, field):
                date_str = getattr(entry, field)
                if date_str:
                    try:
                        return parsedate_to_datetime(date_str)
                    except (TypeError, ValueError):
                        pass
        
        return None
    
    @staticmethod
    def parse_feed(feed_content: str) -> List[RSSEntry]:
        """
        Parse RSS feed content and extract entries.
        
        Args:
            feed_content: Raw RSS feed XML content
            
        Returns:
            List of parsed RSS entries
        """
        parsed = feedparser.parse(feed_content)
        entries = []
        
        if parsed.bozo and not parsed.entries:
            # Feed is malformed and has no entries
            raise ValueError(f"Failed to parse RSS feed: {parsed.get('bozo_exception', 'Unknown error')}")
        
        for entry in parsed.entries:
            try:
                # Extract required fields
                title = entry.get('title', '').strip()
                url = entry.get('link', '').strip()
                
                if not title or not url:
                    continue  # Skip entries without title or URL
                
                # Extract optional fields
                summary = entry.get('summary', entry.get('description', '')).strip()
                published_at = RSSParser.parse_published_date(entry)
                
                entries.append(RSSEntry(
                    title=title,
                    url=url,
                    published_at=published_at,
                    summary=summary or None,
                ))
            except Exception as e:
                # Log but don't fail entire feed for one bad entry
                print(f"Warning: Failed to parse entry: {e}")
                continue
        
        return entries
    
    @staticmethod
    def compute_content_hash(title: str, url: str, summary: Optional[str] = None) -> str:
        """
        Compute SHA256 hash of article content for deduplication.
        
        Args:
            title: Article title
            url: Article URL
            summary: Optional article summary
            
        Returns:
            Hexadecimal hash string
        """
        content = f"{title}|{url}|{summary or ''}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
