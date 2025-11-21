"""Extractive summarizer using simple text extraction."""

import re
from ..models import Article
from .base import BaseSummarizer


class ExtractiveSummarizer(BaseSummarizer):
    """Simple extractive summarizer that extracts key sentences."""

    def __init__(self, max_sentences: int = 2, max_chars: int = 300):
        self.max_sentences = max_sentences
        self.max_chars = max_chars

    async def summarize(self, article: Article) -> str:
        """Extract the first few sentences as a summary."""
        # Use description if available, otherwise use content
        text = article.description or article.content or article.title or ""

        if not text:
            return ""

        # Clean the text
        text = re.sub(r"\s+", " ", text).strip()

        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)

        # Take the first N sentences
        summary_sentences = sentences[: self.max_sentences]
        summary = " ".join(summary_sentences)

        # Truncate if too long
        if len(summary) > self.max_chars:
            summary = summary[: self.max_chars - 3] + "..."

        return summary
