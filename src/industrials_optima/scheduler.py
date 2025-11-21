"""Scheduler for daily digest generation."""

import asyncio
import logging
import schedule
import time
from datetime import datetime

from .aggregator import NewsAggregator
from .config import get_config
from .output import DigestFormatter, EmailSender

logger = logging.getLogger(__name__)


async def generate_and_deliver():
    """Generate digest and deliver via configured methods."""
    config = get_config()
    aggregator = NewsAggregator(config)
    formatter = DigestFormatter()

    logger.info(f"Starting digest generation at {datetime.now()}")

    try:
        # Generate digest
        digest = await aggregator.create_daily_digest()

        # Save to files
        saved_files = formatter.save(digest, config.output_dir)
        for f in saved_files:
            logger.info(f"Saved digest to: {f}")

        # Send email if configured
        if config.email_to:
            email_sender = EmailSender(config)
            if email_sender.send(digest):
                logger.info("Digest email sent successfully")
            else:
                logger.warning("Failed to send digest email")

        # Print summary to console
        print("\n" + "=" * 60)
        print(f"INDUSTRIALS OPTIMA DAILY DIGEST - {digest.date.strftime('%Y-%m-%d')}")
        print("=" * 60)

        for topic in digest.topics:
            print(f"\n{topic.topic_name}: {len(topic.articles)} articles")
            for article in topic.articles[:3]:  # Show first 3
                print(f"  - {article.title[:60]}...")

        print("\n" + "=" * 60)
        print(f"Full digest saved to: {config.output_dir}")
        print("=" * 60 + "\n")

        return digest

    except Exception as e:
        logger.error(f"Error generating digest: {e}")
        raise


def run_sync():
    """Synchronous wrapper for the async generation function."""
    asyncio.run(generate_and_deliver())


def start_scheduler(delivery_time: str = None):
    """Start the scheduler for daily digest delivery."""
    config = get_config()
    delivery_time = delivery_time or config.delivery_time

    logger.info(f"Scheduling daily digest for {delivery_time}")

    schedule.every().day.at(delivery_time).do(run_sync)

    print(f"Industrials Optima scheduler started.")
    print(f"Daily digest will be generated at {delivery_time}")
    print("Press Ctrl+C to stop.\n")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
