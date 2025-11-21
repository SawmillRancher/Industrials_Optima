"""Main news aggregator that combines all fetchers and summarizers."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from .config import TOPICS, TopicConfig, AppConfig, get_config
from .models import Article, TopicDigest, DailyDigest
from .fetchers import RSSFetcher, NewsAPIFetcher
from .summarizers import get_summarizer

logger = logging.getLogger(__name__)


class NewsAggregator:
    """Main aggregator that fetches, filters, and summarizes news."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_config()
        self.topics = TOPICS

        # Initialize fetchers
        self.rss_fetcher = RSSFetcher(lookback_hours=24)
        self.newsapi_fetcher = (
            NewsAPIFetcher(api_key=self.config.newsapi_key, lookback_hours=24)
            if self.config.newsapi_key
            else None
        )

        # Initialize summarizer
        self.summarizer = get_summarizer(
            self.config.summarizer,
            openai_key=self.config.openai_api_key,
            anthropic_key=self.config.anthropic_api_key,
        )

    async def fetch_topic(self, topic: TopicConfig) -> list[Article]:
        """Fetch articles for a single topic from all sources."""
        all_articles = []

        # Fetch from RSS feeds
        try:
            rss_articles = await self.rss_fetcher.fetch(topic)
            all_articles.extend(rss_articles)
            logger.info(f"RSS: {len(rss_articles)} articles for {topic.name}")
        except Exception as e:
            logger.error(f"RSS fetch error for {topic.name}: {e}")

        # Fetch from NewsAPI if available
        if self.newsapi_fetcher:
            try:
                newsapi_articles = await self.newsapi_fetcher.fetch(topic)
                all_articles.extend(newsapi_articles)
                logger.info(f"NewsAPI: {len(newsapi_articles)} articles for {topic.name}")
            except Exception as e:
                logger.error(f"NewsAPI fetch error for {topic.name}: {e}")

        # Deduplicate by URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)

        # Sort by relevance and recency
        unique_articles.sort(
            key=lambda a: (a.relevance_score, a.published or datetime.min),
            reverse=True,
        )

        # Limit to max articles
        return unique_articles[: self.config.max_articles_per_topic]

    async def create_topic_digest(self, topic: TopicConfig) -> TopicDigest:
        """Create a digest for a single topic."""
        articles = await self.fetch_topic(topic)

        # Summarize articles
        if articles:
            articles = await self.summarizer.summarize_batch(articles)

        return TopicDigest(
            topic_name=topic.name,
            topic_description=topic.description,
            articles=articles,
        )

    async def create_daily_digest(self) -> DailyDigest:
        """Create a complete daily digest for all topics."""
        logger.info("Starting daily digest generation...")

        # Fetch all topics concurrently
        tasks = [self.create_topic_digest(topic) for topic in self.topics]
        topic_digests = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors
        valid_digests = []
        for i, result in enumerate(topic_digests):
            if isinstance(result, Exception):
                logger.error(f"Error creating digest for {self.topics[i].name}: {result}")
            else:
                valid_digests.append(result)

        digest = DailyDigest(
            date=datetime.now(),
            topics=valid_digests,
        )

        total_articles = sum(len(td.articles) for td in valid_digests)
        logger.info(
            f"Daily digest complete: {len(valid_digests)} topics, {total_articles} total articles"
        )

        return digest
