"""News fetchers for various sources."""

from .base import BaseFetcher
from .rss import RSSFetcher
from .newsapi import NewsAPIFetcher

__all__ = ["BaseFetcher", "RSSFetcher", "NewsAPIFetcher"]
