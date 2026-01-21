"""
Embedding provider interfaces and implementations.
"""

from abc import ABC, abstractmethod
from typing import List
import httpx
import numpy as np

from app.settings import settings


class EmbeddingProvider(ABC):
    """
    Abstract interface for text embedding providers.
    """
    
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (each vector is a list of floats)
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            Embedding dimension
        """
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    OpenAI embedding provider using text-embedding-3-small model.
    """
    
    def __init__(
        self,
        api_key: str = None,
        model: str = "text-embedding-3-small",
        dimension: int = 1536,
    ):
        """
        Initialize OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
            model: OpenAI embedding model name
            dimension: Embedding dimension
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self.dimension = dimension
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using OpenAI API.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "input": texts,
                    "model": self.model,
                    "dimensions": self.dimension,
                },
            )
            response.raise_for_status()
            
            data = response.json()
            embeddings = [item["embedding"] for item in data["data"]]
            
            return embeddings
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension


class FakeEmbeddingProvider(EmbeddingProvider):
    """
    Fake embedding provider for testing.
    Generates deterministic random embeddings based on text hash.
    """
    
    def __init__(self, dimension: int = 1536):
        """
        Initialize fake embedding provider.
        
        Args:
            dimension: Embedding dimension
        """
        self.dimension = dimension
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate fake embeddings using deterministic random vectors.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of fake embedding vectors
        """
        embeddings = []
        
        for text in texts:
            # Use hash of text as seed for reproducibility
            seed = hash(text) % (2**32)
            rng = np.random.RandomState(seed)
            
            # Generate random vector
            vector = rng.randn(self.dimension).astype(float)
            
            # Normalize to unit length (cosine similarity friendly)
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            
            embeddings.append(vector.tolist())
        
        return embeddings
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension
