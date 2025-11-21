"""Base fetcher interface."""

from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime, timedelta

from ..models import Article
from ..config import TopicConfig


class BaseFetcher(ABC):
    """Abstract base class for news fetchers."""

    def __init__(self, lookback_hours: int = 24):
        """Initialize fetcher with lookback period."""
        self.lookback_hours = lookback_hours
        self.cutoff_date = datetime.now() - timedelta(hours=lookback_hours)

    @abstractmethod
    async def fetch(self, topic: TopicConfig) -> list[Article]:
        """Fetch articles for a given topic."""
        pass

    def is_recent(self, published: Optional[datetime]) -> bool:
        """Check if article is within lookback period."""
        if published is None:
            return True  # Include if no date
        return published >= self.cutoff_date

    def calculate_relevance(self, article: Article, topic: TopicConfig) -> float:
        """Calculate relevance score based on keyword matches."""
        text = f"{article.title or ''} {article.description or ''} {article.content or ''}".lower()
        matches = sum(1 for kw in topic.keywords if kw.lower() in text)
        return matches / len(topic.keywords) if topic.keywords else 0.0
