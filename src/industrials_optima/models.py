"""Data models for news articles."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Article:
    """Represents a news article."""

    title: str
    url: str
    source: str
    published: Optional[datetime] = None
    description: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    topic: Optional[str] = None
    relevance_score: float = 0.0

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        if isinstance(other, Article):
            return self.url == other.url
        return False


@dataclass
class TopicDigest:
    """A digest of articles for a specific topic."""

    topic_name: str
    topic_description: str
    articles: list[Article] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class DailyDigest:
    """Complete daily digest with all topics."""

    date: datetime
    topics: list[TopicDigest] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
