"""
Chat provider interfaces and implementations for RAG.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import httpx

from app.settings import settings


class ChatProvider(ABC):
    """
    Abstract interface for chat completion providers.
    """
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate a chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        pass


class OpenAIChatProvider(ChatProvider):
    """
    OpenAI chat completion provider using GPT-4.
    """
    
    def __init__(
        self,
        api_key: str = None,
        model: str = "gpt-4o-mini",
    ):
        """
        Initialize OpenAI chat provider.
        
        Args:
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
            model: OpenAI model name
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate chat completion using OpenAI API.
        
        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            
        Returns:
            Generated response text
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]


class FakeChatProvider(ChatProvider):
    """
    Fake chat provider for testing.
    Returns predefined responses based on context.
    """
    
    def __init__(self, predefined_response: str = None):
        """
        Initialize fake chat provider.
        
        Args:
            predefined_response: Optional predefined response to return
        """
        self.predefined_response = predefined_response
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate fake response.
        
        Args:
            messages: List of message dicts
            temperature: Ignored
            max_tokens: Ignored
            
        Returns:
            Fake response
        """
        if self.predefined_response:
            return self.predefined_response
        
        # Generate a simple response based on context
        # Find the user question
        user_message = None
        for msg in messages:
            if msg["role"] == "user":
                user_message = msg["content"]
                break
        
        if not user_message:
            return "I don't have enough information to answer."
        
        # Check if context was provided (look for "Context:" in system message)
        has_context = False
        for msg in messages:
            if msg["role"] == "system" and "Context:" in msg["content"]:
                has_context = True
                break
        
        if not has_context:
            return "I don't have enough information in the ingested corpus to answer this question."
        
        # Generate a simple fake answer with citations
        return "Based on the provided context, here is the answer [1]. Additional information can be found in [2]."
