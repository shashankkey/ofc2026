# Glean + Elasticsearch configuration

GLEAN_INSTANCE_URL = "https://your-instance-be.glean.com"  # e.g. https://mycompany-be.glean.com
GLEAN_API_TOKEN = "your-glean-api-token"

ES_HOST = "https://your-elasticsearch-host:9200"
ES_API_KEY = "your-elasticsearch-api-key"  # base64 encoded id:api_key

# Insights request config
DAYS_FROM_NOW_START = 30  # rolling 30-day window
DAYS_FROM_NOW_END = 0

# Elasticsearch index names
INDEX_OVERVIEW = "glean-insights-overview"
INDEX_ASSISTANT = "glean-insights-assistant"
INDEX_AGENTS = "glean-insights-agents"
