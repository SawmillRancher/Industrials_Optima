"""Configuration for news topics and sources."""

from dataclasses import dataclass, field
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TopicConfig:
    """Configuration for a news topic."""

    name: str
    description: str
    keywords: list[str]
    rss_feeds: list[str] = field(default_factory=list)
    newsapi_query: Optional[str] = None


# Define all industrial topics
TOPICS: list[TopicConfig] = [
    TopicConfig(
        name="AI Data Centers",
        description="AI related data center development, expansion, and infrastructure",
        keywords=[
            "AI data center",
            "artificial intelligence data center",
            "hyperscale data center",
            "GPU cluster",
            "AI infrastructure",
            "data center construction",
            "data center expansion",
            "colocation AI",
            "NVIDIA data center",
            "cloud AI infrastructure",
        ],
        rss_feeds=[
            "https://www.datacenterknowledge.com/rss.xml",
            "https://www.datacenterdynamics.com/en/rss/",
        ],
        newsapi_query='("AI data center" OR "artificial intelligence data center" OR "hyperscale" OR "GPU cluster")',
    ),
    TopicConfig(
        name="Global Power Consumption",
        description="Power consumption trends, energy demand, and grid developments globally",
        keywords=[
            "power consumption",
            "energy demand",
            "electricity demand",
            "grid capacity",
            "power grid",
            "energy consumption",
            "megawatt",
            "gigawatt",
            "power shortage",
            "electricity prices",
        ],
        rss_feeds=[
            "https://www.utilitydive.com/feeds/news/",
            "https://www.power-eng.com/feed/",
        ],
        newsapi_query='("power consumption" OR "energy demand" OR "electricity demand" OR "grid capacity")',
    ),
    TopicConfig(
        name="Nuclear Power Industry",
        description="Nuclear power plants, reactors, uranium, and nuclear energy policy",
        keywords=[
            "nuclear power",
            "nuclear reactor",
            "uranium",
            "nuclear plant",
            "SMR",
            "small modular reactor",
            "nuclear energy",
            "atomic energy",
            "nuclear construction",
            "NRC",
        ],
        rss_feeds=[
            "https://www.world-nuclear-news.org/rss",
            "https://www.nei.org/news/feed",
        ],
        newsapi_query='("nuclear power" OR "nuclear reactor" OR "uranium" OR "small modular reactor" OR "SMR")',
    ),
    TopicConfig(
        name="Aerospace Aftermarket & MRO",
        description="Commercial aerospace aftermarket, MRO services, and passenger aviation",
        keywords=[
            "MRO",
            "maintenance repair overhaul",
            "aerospace aftermarket",
            "aircraft maintenance",
            "engine overhaul",
            "aviation MRO",
            "aircraft parts",
            "airline maintenance",
            "CFM",
            "Pratt Whitney",
            "GE Aerospace",
        ],
        rss_feeds=[
            "https://www.aviationweek.com/rss/mro",
            "https://www.mro-network.com/rss.xml",
            "https://www.flightglobal.com/rss",
        ],
        newsapi_query='("MRO" OR "maintenance repair overhaul" OR "aerospace aftermarket" OR "aircraft maintenance")',
    ),
    TopicConfig(
        name="Global Defense",
        description="Major defense announcements, program orders, awards, and contracts",
        keywords=[
            "defense contract",
            "defense award",
            "military contract",
            "Pentagon contract",
            "defense order",
            "defense procurement",
            "Lockheed Martin",
            "Raytheon",
            "Northrop Grumman",
            "BAE Systems",
            "defense program",
        ],
        rss_feeds=[
            "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml",
            "https://breakingdefense.com/feed/",
            "https://www.janes.com/feeds/news",
        ],
        newsapi_query='("defense contract" OR "defense award" OR "military contract" OR "Pentagon" OR "defense procurement")',
    ),
    TopicConfig(
        name="Freight Transportation",
        description="Freight news including bankruptcies, demand trends, and trucking",
        keywords=[
            "freight",
            "trucking",
            "freight demand",
            "freight rates",
            "trucking bankruptcy",
            "logistics",
            "LTL",
            "truckload",
            "freight recession",
            "freight volume",
            "carrier bankruptcy",
        ],
        rss_feeds=[
            "https://www.freightwaves.com/news/rss",
            "https://www.ttnews.com/rss.xml",
            "https://www.supplychaindive.com/feeds/news/",
        ],
        newsapi_query='("freight" OR "trucking" OR "freight demand" OR "trucking bankruptcy" OR "LTL")',
    ),
    TopicConfig(
        name="Airfreight",
        description="Airfreight rates, air cargo trends, and cargo capacity",
        keywords=[
            "airfreight",
            "air cargo",
            "cargo rates",
            "air freight rates",
            "cargo capacity",
            "freighter aircraft",
            "cargo airline",
            "air cargo demand",
            "belly cargo",
        ],
        rss_feeds=[
            "https://www.aircargonews.net/feed/",
            "https://theloadstar.com/feed/",
        ],
        newsapi_query='("airfreight" OR "air cargo" OR "air freight rates" OR "cargo capacity")',
    ),
    TopicConfig(
        name="Ocean Shipping",
        description="Ocean shipping trends, container rates, and maritime logistics",
        keywords=[
            "ocean shipping",
            "container shipping",
            "container rates",
            "maritime",
            "shipping rates",
            "TEU",
            "port congestion",
            "Maersk",
            "MSC",
            "ocean freight",
            "bulk shipping",
        ],
        rss_feeds=[
            "https://www.seatrade-maritime.com/rss.xml",
            "https://gcaptain.com/feed/",
            "https://splash247.com/feed/",
        ],
        newsapi_query='("ocean shipping" OR "container shipping" OR "container rates" OR "maritime logistics")',
    ),
]


@dataclass
class AppConfig:
    """Application configuration."""

    # API Keys
    newsapi_key: Optional[str] = field(default_factory=lambda: os.getenv("NEWSAPI_KEY"))
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))

    # Email settings (optional)
    smtp_server: Optional[str] = field(default_factory=lambda: os.getenv("SMTP_SERVER"))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    smtp_username: Optional[str] = field(default_factory=lambda: os.getenv("SMTP_USERNAME"))
    smtp_password: Optional[str] = field(default_factory=lambda: os.getenv("SMTP_PASSWORD"))
    email_from: Optional[str] = field(default_factory=lambda: os.getenv("EMAIL_FROM"))
    email_to: Optional[str] = field(default_factory=lambda: os.getenv("EMAIL_TO"))

    # Summarization settings
    summarizer: str = field(
        default_factory=lambda: os.getenv("SUMMARIZER", "extractive")
    )  # extractive, openai, anthropic
    max_articles_per_topic: int = field(
        default_factory=lambda: int(os.getenv("MAX_ARTICLES_PER_TOPIC", "10"))
    )

    # Schedule settings
    delivery_time: str = field(
        default_factory=lambda: os.getenv("DELIVERY_TIME", "07:00")
    )  # 24h format

    # Output settings
    output_dir: str = field(default_factory=lambda: os.getenv("OUTPUT_DIR", "./output"))


def get_config() -> AppConfig:
    """Get application configuration."""
    return AppConfig()
