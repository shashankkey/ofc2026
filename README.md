# Aternity → Elasticsearch Ingestion Pipeline

Pulls **BUSINESS_ACTIVITIES_HOURLY** data from Aternity's OData REST API and ingests into an **Elasticsearch 8.17.x data stream**.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your Aternity and Elasticsearch credentials

# 3. Test with dry run
python aternity_to_elastic.py --dry-run

# 4. Run
python aternity_to_elastic.py
```

## Usage

```bash
# Pull since last checkpoint (or last 24h on first run)
python aternity_to_elastic.py

# Pull last 48 hours (ignores checkpoint)
python aternity_to_elastic.py --hours 48

# Dry run — fetch from Aternity, don't ingest
python aternity_to_elastic.py --dry-run
```

## Cron Setup

Run every hour:
```cron
0 * * * * /usr/bin/python3 /opt/aternity/aternity_to_elastic.py >> /var/log/aternity_ingestion.log 2>&1
```

## How It Works

1. **Checkpoint-based**: Tracks the last ingested timestamp in `.aternity_checkpoint`
2. **Deduplication**: Generates deterministic document IDs to prevent duplicates on re-runs
3. **Pagination**: Handles OData pagination automatically
4. **Data Stream**: Uses Elasticsearch data streams (`metrics-aternity.business_activities-default`)
5. **Default mappings**: No explicit mappings — uses Elasticsearch dynamic defaults

## Files

| File | Purpose |
|---|---|
| `aternity_to_elastic.py` | Main ingestion script |
| `.env.example` | Environment variable template |
| `.env` | Your actual config (git-ignored) |
| `.aternity_checkpoint` | Auto-managed timestamp file |
| `requirements.txt` | Python dependencies |
