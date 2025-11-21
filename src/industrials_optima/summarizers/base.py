"""Base summarizer interface."""

from abc import ABC, abstractmethod

from ..models import Article


class BaseSummarizer(ABC):
    """Abstract base class for article summarizers."""

    @abstractmethod
    async def summarize(self, article: Article) -> str:
        """Generate a summary for an article."""
        pass

    async def summarize_batch(self, articles: list[Article]) -> list[Article]:
        """Summarize a batch of articles."""
        for article in articles:
            if not article.summary:
                article.summary = await self.summarize(article)
        return articles
