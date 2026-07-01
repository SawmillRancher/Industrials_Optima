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

## SEC Financial Model Builder (`secmodel`)

`industrials_optima.secmodel` builds a **DSV-style, formula-driven equity model**
in Excel, sourced **exclusively from SEC EDGAR filings**. The included builder
targets **Copart, Inc. (CPRT)**.

```bash
copart-model --out models/Copart_SEC_Model.xlsx
# or
python -m industrials_optima.secmodel.build --out models/Copart_SEC_Model.xlsx
```

What it produces (`models/Copart_SEC_Model.xlsx`):

- **15 fiscal years** of history (FY2011–FY2025), each with `Q1 · Q2 · Q3 · Q4 ·
  FY` columns, plus **FY2026E–FY2030E** driver-based forecast columns.
- **All reported segments** — United States and International — with revenue,
  operating income, margins, assets, D&A, CapEx and goodwill by segment.
- Consolidated income statement (with the noncontrolling-interest split so net
  income attributable and EPS tie to the press release), cash flow, balance
  sheet, ratio analysis (ROE / ROIC / DuPont / net-debt-to-EBITDA) and valuation.
- **Non-GAAP reconciliation** exactly as Copart reported it in its 8-K earnings
  releases (Item 2.02, Exhibit 99.1): GAAP net income → itemized adjustments →
  non-GAAP net income and non-GAAP diluted EPS, per quarter and fiscal year for
  FY2016–FY2023 (Copart reverted to GAAP-only reporting from FY2024).
- A `Bull-Base-Bear` scenario summary and an unlevered `DCF` sheet.
- Formatting/convention mirrors an institutional template: **blue = as-reported
  SEC input, black = live formula, pale-yellow columns = forecast** driven by an
  on-sheet Assumptions / scenario table (toggle Bull/Base/Bear).

Data sources (SEC EDGAR only, CIK `0000900075`):

- Consolidated figures — the XBRL *company facts* API (`data.sec.gov`).
- Segment (US vs International) figures — parsed from the XBRL *instance*
  documents filed with each 10-K / 10-Q (the company-facts API discards the
  segment dimension).

How it is organised:

| Module | Purpose |
| --- | --- |
| `secmodel/edgar.py` | Cached, throttled EDGAR HTTP client |
| `secmodel/xbrl.py` | Minimal XBRL instance parser (periods + dimensions) |
| `secmodel/earnings.py` | Parses non-GAAP reconciliation tables from 8-K press releases |
| `secmodel/model.py` | Assembles consolidated + segment + non-GAAP series |
| `secmodel/workbook.py` | Renders the formatted, formula-driven workbook |
| `secmodel/build.py` | CLI entry point |

> The model uses only SEC-filed financials. The single manual, non-SEC input is
> the valuation share price (clearly flagged on the sheet). Per-share figures are
> as-reported and are **not** retroactively adjusted for stock splits.

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
