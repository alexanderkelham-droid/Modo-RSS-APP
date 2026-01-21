"""
Text chunking service for RAG.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class TextChunk:
    """Represents a text chunk with metadata."""
    text: str
    chunk_index: int
    start_pos: int
    end_pos: int


class ChunkingService:
    """
    Service for splitting text into overlapping chunks.
    """
    
    def __init__(
        self,
        min_chunk_size: int = 800,
        max_chunk_size: int = 1200,
        overlap: int = 100,
    ):
        """
        Initialize chunking service.
        
        Args:
            min_chunk_size: Minimum chunk size in characters
            max_chunk_size: Maximum chunk size in characters
            overlap: Overlap size in characters
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str) -> List[TextChunk]:
        """
        Split text into overlapping chunks.
        
        Strategy:
        1. Try to chunk at sentence boundaries when possible
        2. Fall back to word boundaries if needed
        3. Ensure chunks are between min_chunk_size and max_chunk_size
        4. Add overlap between consecutive chunks
        
        Args:
            text: Text to chunk
            
        Returns:
            List of TextChunk objects
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # Handle very short text
        if len(text) <= self.max_chunk_size:
            return [TextChunk(
                text=text,
                chunk_index=0,
                start_pos=0,
                end_pos=len(text)
            )]
        
        chunks = []
        chunk_index = 0
        start_pos = 0
        
        while start_pos < len(text):
            # Determine end position for this chunk
            end_pos = min(start_pos + self.max_chunk_size, len(text))
            
            # If this is not the last chunk, try to find a good break point
            if end_pos < len(text):
                # Try to break at sentence boundary (., !, ?)
                chunk_text = text[start_pos:end_pos]
                
                # Look for sentence endings in the last 200 chars
                search_start = max(0, len(chunk_text) - 200)
                last_sentence_end = max(
                    chunk_text.rfind('. ', search_start),
                    chunk_text.rfind('! ', search_start),
                    chunk_text.rfind('? ', search_start),
                )
                
                if last_sentence_end != -1 and last_sentence_end > self.min_chunk_size:
                    # Break at sentence boundary
                    end_pos = start_pos + last_sentence_end + 1
                else:
                    # Fall back to word boundary
                    chunk_text = text[start_pos:end_pos]
                    last_space = chunk_text.rfind(' ')
                    
                    if last_space > self.min_chunk_size:
                        end_pos = start_pos + last_space
            
            # Extract chunk text
            chunk_text = text[start_pos:end_pos].strip()
            
            if chunk_text:  # Only add non-empty chunks
                chunks.append(TextChunk(
                    text=chunk_text,
                    chunk_index=chunk_index,
                    start_pos=start_pos,
                    end_pos=end_pos
                ))
                chunk_index += 1
            
            # Move to next chunk with overlap
            if end_pos >= len(text):
                break
            
            # Calculate next start position with overlap
            start_pos = end_pos - self.overlap
            
            # Ensure we're making progress
            if start_pos <= chunks[-1].start_pos if chunks else 0:
                start_pos = end_pos
        
        return chunks
    
    def chunk_article(
        self,
        content_text: str,
        article_metadata: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Chunk article content and attach metadata.
        
        Args:
            content_text: Article content text
            article_metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        chunks = self.chunk_text(content_text)
        
        result = []
        for chunk in chunks:
            chunk_dict = {
                "text": chunk.text,
                "chunk_index": chunk.chunk_index,
            }
            
            # Attach metadata if provided
            if article_metadata:
                chunk_dict.update(article_metadata)
            
            result.append(chunk_dict)
        
        return result
