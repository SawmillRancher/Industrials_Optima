"""NewsAPI fetcher."""

import logging
from datetime import datetime, timedelta
from typing import Optional

import aiohttp
from dateutil import parser as date_parser
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import Article
from ..config import TopicConfig
from .base import BaseFetcher

logger = logging.getLogger(__name__)


class NewsAPIFetcher(BaseFetcher):
    """Fetches news from NewsAPI.org."""

    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self, api_key: str, lookback_hours: int = 24, timeout: int = 30):
        super().__init__(lookback_hours)
        self.api_key = api_key
        self.timeout = timeout

    async def fetch(self, topic: TopicConfig) -> list[Article]:
        """Fetch articles from NewsAPI for a topic."""
        if not topic.newsapi_query:
            return []

        articles = []
        from_date = (datetime.now() - timedelta(hours=self.lookback_hours)).strftime("%Y-%m-%d")

        try:
            articles = await self._fetch_query(topic.newsapi_query, from_date, topic)
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI for {topic.name}: {e}")

        return articles

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _fetch_query(
        self, query: str, from_date: str, topic: TopicConfig
    ) -> list[Article]:
        """Execute NewsAPI query."""
        articles = []

        params = {
            "q": query,
            "from": from_date,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 50,
            "apiKey": self.api_key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.BASE_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.warning(f"NewsAPI returned status {response.status}: {error_text}")
                    return []

                data = await response.json()

        if data.get("status") != "ok":
            logger.warning(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            return []

        for item in data.get("articles", []):
            published = self._parse_date(item.get("publishedAt"))

            if not self.is_recent(published):
                continue

            article = Article(
                title=item.get("title", "").strip(),
                url=item.get("url", ""),
                source=item.get("source", {}).get("name", "NewsAPI"),
                published=published,
                description=item.get("description", ""),
                content=item.get("content", ""),
                topic=topic.name,
            )

            article.relevance_score = self.calculate_relevance(article, topic)
            articles.append(article)

        logger.info(f"Fetched {len(articles)} articles from NewsAPI for {topic.name}")
        return articles

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO date string to datetime."""
        if not date_str:
            return None
        try:
            return date_parser.parse(date_str)
        except (ValueError, TypeError):
            return None
