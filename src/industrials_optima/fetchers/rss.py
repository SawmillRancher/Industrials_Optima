"""RSS feed fetcher."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

import aiohttp
import feedparser
from dateutil import parser as date_parser
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import Article
from ..config import TopicConfig
from .base import BaseFetcher

logger = logging.getLogger(__name__)


class RSSFetcher(BaseFetcher):
    """Fetches news from RSS feeds."""

    def __init__(self, lookback_hours: int = 24, timeout: int = 30):
        super().__init__(lookback_hours)
        self.timeout = timeout

    async def fetch(self, topic: TopicConfig) -> list[Article]:
        """Fetch articles from all RSS feeds for a topic."""
        if not topic.rss_feeds:
            return []

        tasks = [self._fetch_feed(url, topic) for url in topic.rss_feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error fetching RSS feed: {result}")
            else:
                articles.extend(result)

        # Deduplicate by URL
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)

        return unique_articles

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _fetch_feed(self, feed_url: str, topic: TopicConfig) -> list[Article]:
        """Fetch and parse a single RSS feed."""
        articles = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    feed_url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    headers={"User-Agent": "IndustrialsOptima/1.0"},
                ) as response:
                    if response.status != 200:
                        logger.warning(f"RSS feed {feed_url} returned status {response.status}")
                        return []

                    content = await response.text()

            feed = feedparser.parse(content)

            for entry in feed.entries:
                published = self._parse_date(entry.get("published") or entry.get("updated"))

                if not self.is_recent(published):
                    continue

                article = Article(
                    title=entry.get("title", "").strip(),
                    url=entry.get("link", ""),
                    source=feed.feed.get("title", feed_url),
                    published=published,
                    description=self._clean_html(entry.get("summary", "")),
                    content=self._clean_html(entry.get("content", [{}])[0].get("value", ""))
                    if entry.get("content")
                    else None,
                    topic=topic.name,
                )

                # Calculate relevance and filter
                article.relevance_score = self.calculate_relevance(article, topic)
                if article.relevance_score > 0:
                    articles.append(article)

            logger.info(f"Fetched {len(articles)} relevant articles from {feed_url}")

        except Exception as e:
            logger.error(f"Error parsing RSS feed {feed_url}: {e}")
            raise

        return articles

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        try:
            return date_parser.parse(date_str)
        except (ValueError, TypeError):
            return None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(text, "lxml")
        return soup.get_text(separator=" ", strip=True)
