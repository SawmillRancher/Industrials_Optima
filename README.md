# Industrials Optima

A news aggregator for industrial sectors that delivers a summarized daily digest of the latest developments in:

- **AI Data Centers** - Data center development, expansion, and AI infrastructure
- **Global Power Consumption** - Energy demand, grid developments, and electricity trends
- **Nuclear Power Industry** - Nuclear plants, reactors, uranium, and SMR developments
- **Aerospace Aftermarket & MRO** - Aircraft maintenance, repair, overhaul services
- **Global Defense** - Defense contracts, program awards, and procurement
- **Freight Transportation** - Trucking, freight demand, bankruptcies
- **Airfreight** - Air cargo rates and capacity trends
- **Ocean Shipping** - Container shipping rates and maritime logistics

## Features

- Multi-source news aggregation (RSS feeds + NewsAPI)
- Configurable AI-powered or extractive summarization
- Daily scheduled digest delivery
- Email delivery support
- HTML and Markdown output formats
- Keyword-based relevance scoring

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd Industrials_Optima

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings:

```bash
# Required for NewsAPI (get free key from https://newsapi.org/)
NEWSAPI_KEY=your_newsapi_key

# Optional: For AI-powered summarization
OPENAI_API_KEY=your_openai_key
# OR
ANTHROPIC_API_KEY=your_anthropic_key

# Summarizer type: extractive (default), openai, or anthropic
SUMMARIZER=extractive

# Delivery time (24-hour format)
DELIVERY_TIME=07:00

# Output directory
OUTPUT_DIR=./output
```

### Email Configuration (Optional)

To receive digests via email:

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=recipient@example.com
```

For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833).

## Usage

### Generate Digest Immediately

```bash
industrials-optima run
```

Or run directly with Python:

```bash
python -m industrials_optima.cli run
```

### Start Daily Scheduler

```bash
# Default time (7:00 AM)
industrials-optima schedule

# Custom time
industrials-optima schedule -t 06:30
```

### View Configured Topics

```bash
industrials-optima topics
```

### Check Configuration

```bash
industrials-optima config
```

## Output

Digests are saved to the output directory (default: `./output`) in both:
- Markdown format: `digest_YYYY-MM-DD.md`
- HTML format: `digest_YYYY-MM-DD.html`

## Running as a Service

### Using systemd (Linux)

Create `/etc/systemd/system/industrials-optima.service`:

```ini
[Unit]
Description=Industrials Optima News Aggregator
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/Industrials_Optima
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/industrials-optima schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable industrials-optima
sudo systemctl start industrials-optima
```

### Using cron

Add to crontab (`crontab -e`):

```bash
0 7 * * * cd /path/to/Industrials_Optima && /path/to/venv/bin/industrials-optima run
```

## Customizing Topics

Edit `src/industrials_optima/config.py` to modify topics, keywords, or add new RSS feeds.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff src/
```

## License

MIT
