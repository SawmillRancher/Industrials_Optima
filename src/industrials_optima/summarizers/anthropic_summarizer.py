"""Anthropic Claude-based summarizer."""

import logging
from anthropic import AsyncAnthropic

from ..models import Article
from .base import BaseSummarizer

logger = logging.getLogger(__name__)


class AnthropicSummarizer(BaseSummarizer):
    """Summarizer using Anthropic's Claude models."""

    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def summarize(self, article: Article) -> str:
        """Generate a summary using Claude."""
        text = article.description or article.content or article.title or ""

        if not text or len(text) < 50:
            return text

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=150,
                messages=[
                    {
                        "role": "user",
                        "content": f"You are a business news analyst. Summarize this news article in 1-2 concise sentences, focusing on key facts and business implications. Be direct and factual.\n\nTitle: {article.title}\n\nContent: {text[:2000]}",
                    },
                ],
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Anthropic summarization error: {e}")
            # Fall back to extractive
            from .extractive import ExtractiveSummarizer

            fallback = ExtractiveSummarizer()
            return await fallback.summarize(article)
