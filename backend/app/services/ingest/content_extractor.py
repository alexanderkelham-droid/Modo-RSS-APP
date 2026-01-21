"""
Article content extraction using readability-lxml and BeautifulSoup.
"""

import httpx
from typing import Optional, Tuple
from bs4 import BeautifulSoup
from readability import Document
from langdetect import detect, LangDetectException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.settings import settings


class ContentExtractionError(Exception):
    """Raised when content extraction fails."""
    pass


class ContentExtractor:
    """Extracts main article content from HTML."""
    
    def __init__(
        self,
        timeout: int = 30,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize content extractor.
        
        Args:
            timeout: Request timeout in seconds
            user_agent: Custom user agent string
        """
        self.timeout = timeout
        self.user_agent = user_agent or settings.USER_AGENT
    
    async def resolve_google_news_url(self, url: str) -> str:
        """
        Resolve Google News redirect URL to actual article URL.
        
        Args:
            url: Google News URL
            
        Returns:
            Actual article URL
        """
        if "news.google.com" not in url:
            return url
        
        try:
            headers = {
                "User-Agent": self.user_agent,
            }
            
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                response = await client.head(url, headers=headers)
                # The final URL after all redirects
                return str(response.url)
        except Exception as e:
            print(f"Failed to resolve Google News URL {url}: {e}")
            # Return original URL as fallback
            return url
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    )
    async def fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from URL with retries.
        
        Args:
            url: Article URL
            
        Returns:
            Raw HTML content
            
        Raises:
            ContentExtractionError: If fetch fails
        """
        # Resolve Google News URLs first
        resolved_url = await self.resolve_google_news_url(url)
        
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Referer": "https://news.google.com/",  # Some sites require this
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(resolved_url, headers=headers)
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as e:
            raise ContentExtractionError(f"HTTP {e.response.status_code}: {resolved_url}") from e
        except httpx.TimeoutException as e:
            raise ContentExtractionError(f"Timeout fetching {resolved_url}") from e
        except httpx.HTTPError as e:
            raise ContentExtractionError(f"HTTP error fetching {resolved_url}: {e}") from e
        except Exception as e:
            raise ContentExtractionError(f"Unexpected error fetching {resolved_url}: {e}") from e
    
    def extract_with_readability(self, html: str) -> Optional[str]:
        """
        Extract main content using readability-lxml.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            doc = Document(html)
            summary_html = doc.summary()
            
            # Parse summary HTML and extract text
            soup = BeautifulSoup(summary_html, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean up whitespace
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up excessive newlines
            lines = [line.strip() for line in text.split('\n')]
            lines = [line for line in lines if line]
            text = '\n\n'.join(lines)
            
            # Only return if we got substantial content
            if len(text) > 100:
                return text
            
            return None
        
        except Exception as e:
            print(f"Readability extraction failed: {e}")
            return None
    
    def extract_with_beautifulsoup(self, html: str) -> Optional[str]:
        """
        Fallback extraction using BeautifulSoup paragraph joining.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove script, style, nav, footer, header elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()
            
            # Find all paragraph tags
            paragraphs = soup.find_all('p')
            
            if not paragraphs:
                return None
            
            # Extract text from paragraphs
            texts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 20:  # Filter out very short paragraphs
                    texts.append(text)
            
            if not texts:
                return None
            
            # Join paragraphs
            content = '\n\n'.join(texts)
            
            # Only return if we got substantial content
            if len(content) > 100:
                return content
            
            return None
        
        except Exception as e:
            print(f"BeautifulSoup extraction failed: {e}")
            return None
    
    def extract_content(self, html: str) -> Optional[str]:
        """
        Extract article content with readability fallback to BeautifulSoup.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Extracted text content or None if all methods fail
        """
        # Try readability first
        content = self.extract_with_readability(html)
        
        if content:
            return content
        
        # Fall back to BeautifulSoup
        print("Readability failed, trying BeautifulSoup fallback...")
        content = self.extract_with_beautifulsoup(html)
        
        return content
    
    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect language of text using langdetect.
        
        Args:
            text: Text content
            
        Returns:
            ISO 639-1 language code or None if detection fails
        """
        if not text or len(text) < 20:
            return None
        
        try:
            # Use first 1000 characters for faster detection
            sample = text[:1000]
            lang = detect(sample)
            return lang
        except LangDetectException as e:
            print(f"Language detection failed: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in language detection: {e}")
            return None
    
    async def extract_article(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Fetch and extract article content with language detection.
        
        Args:
            url: Article URL
            
        Returns:
            Tuple of (content_text, language_code)
            
        Raises:
            ContentExtractionError: If fetch fails
        """
        # Fetch HTML
        html = await self.fetch_html(url)
        
        # Extract content
        content = self.extract_content(html)
        
        # Detect language
        language = None
        if content:
            language = self.detect_language(content)
        
        return content, language
