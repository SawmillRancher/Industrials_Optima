"""OpenAI-based summarizer."""

import logging
from openai import AsyncOpenAI

from ..models import Article
from .base import BaseSummarizer

logger = logging.getLogger(__name__)


class OpenAISummarizer(BaseSummarizer):
    """Summarizer using OpenAI's GPT models."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def summarize(self, article: Article) -> str:
        """Generate a summary using OpenAI."""
        text = article.description or article.content or article.title or ""

        if not text or len(text) < 50:
            return text

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a business news analyst. Summarize the following news article in 1-2 concise sentences, focusing on the key facts and business implications. Be direct and factual.",
                    },
                    {
                        "role": "user",
                        "content": f"Title: {article.title}\n\nContent: {text[:2000]}",
                    },
                ],
                max_tokens=150,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI summarization error: {e}")
            # Fall back to extractive
            from .extractive import ExtractiveSummarizer

            fallback = ExtractiveSummarizer()
            return await fallback.summarize(article)
