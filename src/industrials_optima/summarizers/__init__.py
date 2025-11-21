"""Article summarizers."""

from .base import BaseSummarizer
from .extractive import ExtractiveSummarizer
from .openai_summarizer import OpenAISummarizer
from .anthropic_summarizer import AnthropicSummarizer

__all__ = ["BaseSummarizer", "ExtractiveSummarizer", "OpenAISummarizer", "AnthropicSummarizer"]


def get_summarizer(
    summarizer_type: str, openai_key: str = None, anthropic_key: str = None
) -> BaseSummarizer:
    """Factory function to get the appropriate summarizer."""
    if summarizer_type == "openai" and openai_key:
        return OpenAISummarizer(api_key=openai_key)
    elif summarizer_type == "anthropic" and anthropic_key:
        return AnthropicSummarizer(api_key=anthropic_key)
    else:
        return ExtractiveSummarizer()
