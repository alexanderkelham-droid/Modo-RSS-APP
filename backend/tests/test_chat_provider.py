"""
Tests for chat providers.
"""

import pytest
from app.services.rag.chat_provider import (
    FakeChatProvider,
    OpenAIChatProvider,
)


@pytest.mark.asyncio
async def test_fake_provider_basic():
    """Test fake provider basic functionality."""
    provider = FakeChatProvider()
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Context: Some context here."},
        {"role": "user", "content": "What is this about?"},
    ]
    
    response = await provider.generate(messages)
    
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_fake_provider_with_predefined_response():
    """Test fake provider with predefined response."""
    provider = FakeChatProvider(predefined_response="This is a test response [1].")
    
    messages = [
        {"role": "user", "content": "Any question?"},
    ]
    
    response = await provider.generate(messages)
    
    assert response == "This is a test response [1]."


@pytest.mark.asyncio
async def test_fake_provider_no_context():
    """Test fake provider when no context is provided."""
    provider = FakeChatProvider()
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is this?"},
    ]
    
    response = await provider.generate(messages)
    
    assert "don't have enough information" in response.lower()


@pytest.mark.asyncio
async def test_fake_provider_with_context():
    """Test fake provider with context."""
    provider = FakeChatProvider()
    
    messages = [
        {"role": "system", "content": "Context: Solar energy is renewable. Answer the question."},
        {"role": "user", "content": "What is solar energy?"},
    ]
    
    response = await provider.generate(messages)
    
    # Should generate answer with citations
    assert "[1]" in response or "[2]" in response


@pytest.mark.asyncio
async def test_fake_provider_temperature_ignored():
    """Test that fake provider ignores temperature parameter."""
    provider = FakeChatProvider(predefined_response="Fixed response")
    
    messages = [{"role": "user", "content": "Test"}]
    
    response1 = await provider.generate(messages, temperature=0.0)
    response2 = await provider.generate(messages, temperature=1.0)
    
    # Should be identical since temperature is ignored
    assert response1 == response2


@pytest.mark.asyncio
async def test_openai_provider_requires_api_key():
    """Test that OpenAI provider requires API key."""
    with pytest.raises(ValueError, match="API key is required"):
        OpenAIChatProvider(api_key="")


@pytest.mark.asyncio
async def test_openai_provider_initialization():
    """Test OpenAI provider initialization."""
    provider = OpenAIChatProvider(api_key="test-key", model="gpt-4o-mini")
    
    assert provider.api_key == "test-key"
    assert provider.model == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_fake_provider_empty_messages():
    """Test fake provider with empty messages."""
    provider = FakeChatProvider()
    
    messages = []
    
    response = await provider.generate(messages)
    
    assert "don't have enough information" in response.lower()


@pytest.mark.asyncio
async def test_fake_provider_multiple_user_messages():
    """Test fake provider with multiple messages."""
    provider = FakeChatProvider()
    
    messages = [
        {"role": "system", "content": "Context: Wind energy facts."},
        {"role": "user", "content": "First question"},
        {"role": "assistant", "content": "First answer"},
        {"role": "user", "content": "Second question"},
    ]
    
    response = await provider.generate(messages)
    
    # Should find at least one user message
    assert isinstance(response, str)
    assert len(response) > 0
