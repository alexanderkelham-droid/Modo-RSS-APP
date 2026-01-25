"""
Web scraper service for scraping news from websites without RSS feeds.
"""

from typing import Dict, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import httpx
from abc import ABC, abstractmethod


class ScrapedArticle:
    """Scraped article data."""
    
    def __init__(
        self,
        title: str,
        url: str,
        published_at: Optional[datetime] = None,
        summary: Optional[str] = None,
        image_url: Optional[str] = None,
    ):
        self.title = title
        self.url = url
        self.published_at = published_at
        self.summary = summary
        self.image_url = image_url
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at,
            "summary": self.summary,
            "image_url": self.image_url,
        }
    
    def __repr__(self):
        return f"<ScrapedArticle(title='{self.title[:50]}...', url='{self.url}')>"


class WebScraper(ABC):
    """Base class for website-specific scrapers."""
    
    def __init__(self, base_url: str, name: str):
        """
        Initialize web scraper.
        
        Args:
            base_url: Base URL of the website
            name: Name of the scraper
        """
        self.base_url = base_url
        self.name = name
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    @abstractmethod
    async def scrape_articles(self, max_pages: int = 1) -> List[ScrapedArticle]:
        """
        Scrape articles from the website.
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of scraped articles
        """
        pass
    
    async def fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content
        """
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text


class NESONewsScraper(WebScraper):
    """Scraper for NESO (National Energy System Operator) news page."""
    
    def __init__(self):
        super().__init__(
            base_url="https://www.neso.energy",
            name="NESO News"
        )
        self.news_page_url = f"{self.base_url}/news-and-events"
    
    async def scrape_articles(self, max_pages: int = 3) -> List[ScrapedArticle]:
        """
        Scrape articles from NESO news page.
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of scraped articles
        """
        articles = []
        
        for page_num in range(max_pages):
            # NESO uses ?page=0, ?page=1, etc. for pagination
            url = f"{self.news_page_url}?page={page_num}" if page_num > 0 else self.news_page_url
            
            try:
                html = await self.fetch_html(url)
                page_articles = self._parse_news_page(html)
                
                if not page_articles:
                    # No more articles, stop pagination
                    break
                
                # Fetch image URLs for each article
                for article in page_articles:
                    try:
                        article.image_url = await self._fetch_article_image(article.url)
                    except Exception as e:
                        print(f"Failed to fetch image for {article.url}: {e}")
                
                articles.extend(page_articles)
                print(f"Scraped {len(page_articles)} articles from {url}")
                
            except Exception as e:
                print(f"Error scraping page {page_num}: {e}")
                break
        
        return articles
    
    def _parse_news_page(self, html: str) -> List[ScrapedArticle]:
        """
        Parse NESO news page HTML to extract articles.
        
        Args:
            html: HTML content
            
        Returns:
            List of scraped articles
        """
        soup = BeautifulSoup(html, 'lxml')
        articles = []
        
        # Find all article cards
        article_elements = soup.find_all('article', class_='node--type-article')
        
        seen_urls = set()
        
        for article_elem in article_elements:
            # Find the article link
            link = article_elem.find('a', class_='article-link')
            if not link:
                continue
            
            href = link.get('href', '')
            
            # Only process news articles (skip calendar events)
            if not href.startswith('/news/'):
                continue
            
            # Build full URL
            full_url = f"{self.base_url}{href}"
            
            # Skip duplicates
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)
            
            # Extract title
            title_elem = link.find('h3', class_='article-title')
            title = title_elem.get_text(strip=True) if title_elem else link.get_text(strip=True)
            
            # Extract date/read time
            date_str = None
            published_elem = link.find('p', class_='published-read')
            if published_elem:
                published_text = published_elem.get_text(strip=True)
                # Extract just the date part (before the dash)
                if ' - ' in published_text:
                    date_str = published_text.split(' - ')[0].strip()
                else:
                    date_str = published_text.strip()
            
            # Extract summary/description
            summary = ""
            desc_elem = link.find('div', class_='article-description')
            if desc_elem:
                summary = desc_elem.get_text(strip=True)
            
            # Parse date
            published_at = self._parse_date(date_str) if date_str else None
            
            # Only add if we have a meaningful title
            if title and len(title) > 5:
                article = ScrapedArticle(
                    url=full_url,
                    title=title,
                    published_at=published_at,
                    summary=summary or "",
                )
                articles.append(article)
        
        return articles
        
        return articles
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse NESO date format (e.g., "22 Jan 2026").
        
        Args:
            date_str: Date string
            
        Returns:
            Parsed datetime or None
        """
        from dateutil import parser
        
        try:
            # Use dateutil parser for flexible date parsing
            return parser.parse(date_str)
        except Exception:
            return None
    
    async def _fetch_article_image(self, article_url: str) -> Optional[str]:
        """
        Fetch the main image URL from a NESO article page.
        
        Args:
            article_url: URL of the article
            
        Returns:
            Full image URL or None
        """
        try:
            html = await self.fetch_html(article_url)
            soup = BeautifulSoup(html, 'lxml')
            
            # Find the main article image
            # It's in the image wrapper with class 'field-field-image'
            image_wrapper = soup.find('div', class_='field-field-image')
            if image_wrapper:
                img_tag = image_wrapper.find('img')
                if img_tag and img_tag.get('src'):
                    img_src = img_tag.get('src')
                    # Make it absolute if it's relative
                    if img_src.startswith('/'):
                        return f"{self.base_url}{img_src}"
                    return img_src
            
            return None
        except Exception as e:
            print(f"Error fetching image from {article_url}: {e}")
            return None


# Registry of available scrapers
SCRAPER_REGISTRY = {
    "neso": NESONewsScraper,
}


def get_scraper(scraper_name: str) -> Optional[WebScraper]:
    """
    Get scraper instance by name.
    
    Args:
        scraper_name: Name of the scraper
        
    Returns:
        Scraper instance or None
    """
    scraper_class = SCRAPER_REGISTRY.get(scraper_name.lower())
    if scraper_class:
        return scraper_class()
    return None
