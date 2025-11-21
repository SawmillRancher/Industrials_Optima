"""Command-line interface for Industrials Optima."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from .aggregator import NewsAggregator
from .config import get_config, TOPICS
from .output import DigestFormatter, EmailSender
from .scheduler import start_scheduler, generate_and_deliver


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def cmd_run(args):
    """Run digest generation immediately."""
    setup_logging(args.verbose)
    asyncio.run(generate_and_deliver())


def cmd_schedule(args):
    """Start the scheduler for daily delivery."""
    setup_logging(args.verbose)
    try:
        start_scheduler(args.time)
    except KeyboardInterrupt:
        print("\nScheduler stopped.")


def cmd_topics(args):
    """List configured topics."""
    print("\nConfigured Topics:")
    print("=" * 60)
    for i, topic in enumerate(TOPICS, 1):
        print(f"\n{i}. {topic.name}")
        print(f"   Description: {topic.description}")
        print(f"   Keywords: {', '.join(topic.keywords[:5])}...")
        print(f"   RSS Feeds: {len(topic.rss_feeds)}")
        print(f"   NewsAPI Query: {'Yes' if topic.newsapi_query else 'No'}")
    print()


def cmd_config(args):
    """Show current configuration."""
    config = get_config()
    print("\nCurrent Configuration:")
    print("=" * 60)
    print(f"NewsAPI Key: {'Configured' if config.newsapi_key else 'Not set'}")
    print(f"OpenAI Key: {'Configured' if config.openai_api_key else 'Not set'}")
    print(f"Anthropic Key: {'Configured' if config.anthropic_api_key else 'Not set'}")
    print(f"Summarizer: {config.summarizer}")
    print(f"Max Articles per Topic: {config.max_articles_per_topic}")
    print(f"Delivery Time: {config.delivery_time}")
    print(f"Output Directory: {config.output_dir}")
    print(f"Email Configured: {'Yes' if config.smtp_server and config.email_to else 'No'}")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Industrials Optima - Industrial News Aggregator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  industrials-optima run              Generate digest immediately
  industrials-optima schedule         Start daily scheduler (default 7:00 AM)
  industrials-optima schedule -t 06:30  Start scheduler for 6:30 AM
  industrials-optima topics           List configured topics
  industrials-optima config           Show current configuration
        """,
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Generate digest immediately")
    run_parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    # Schedule command
    schedule_parser = subparsers.add_parser("schedule", help="Start daily scheduler")
    schedule_parser.add_argument(
        "-t", "--time", default=None, help="Delivery time in HH:MM format (default: 07:00)"
    )
    schedule_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    # Topics command
    topics_parser = subparsers.add_parser("topics", help="List configured topics")

    # Config command
    config_parser = subparsers.add_parser("config", help="Show current configuration")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "schedule":
        cmd_schedule(args)
    elif args.command == "topics":
        cmd_topics(args)
    elif args.command == "config":
        cmd_config(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
