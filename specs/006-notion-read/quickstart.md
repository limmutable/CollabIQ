# Quickstart: Notion Read Operations

**Feature**: 006-notion-read
**Estimated Time**: 10-15 minutes
**Prerequisites**: Python 3.12+, UV installed, Notion API access

---

## Overview

This guide will help you set up and use the Notion integration to retrieve company data from your Notion databases.

**What you'll accomplish**:
1. Set up Notion API credentials
2. Configure database IDs
3. Fetch and cache company data
4. Format data for LLM consumption

---

## Step 1: Install Dependencies

```bash
# Add production dependencies
uv add notion-client tenacity

# Add development dependencies (if not already present)
uv add --dev pytest pytest-asyncio
```

**What this does**: Installs the official Notion SDK and retry logic library.

---

## Step 2: Set Up Notion Integration

### 2.1 Create Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Name it "CollabIQ Integration"
4. Select your workspace
5. Set "Content Capabilities" to **Read content** only
6. Copy the "Internal Integration Token" (starts with `secret_`)

### 2.2 Share Databases with Integration

1. Open your "Companies" database in Notion
2. Click "..." menu → "Connections" → "Connect to" → Select your integration
3. Repeat for "CollabIQ" database

**Important**: The integration won't work until databases are explicitly shared!

---

## Step 3: Configure Environment Variables

### 3.1 Get Database IDs

**Method 1: From Notion URL**
```
https://www.notion.so/{workspace}/{database_id}?v={view_id}
                                   ^^^^^^^^^^^^
                                   Copy this part
```

**Method 2: Via API**
```python
from notion_client import Client
client = Client(auth="secret_...")
databases = client.search(filter={"property": "object", "value": "database"})
for db in databases["results"]:
    print(f"{db['title'][0]['plain_text']}: {db['id']}")
```

### 3.2 Add to .env File

```bash
# Add to .env (or Infisical)
NOTION_API_KEY=secret_...
NOTION_DATABASE_ID_COMPANIES=abc123-def456-...
NOTION_DATABASE_ID_COLLABIQ=xyz789-uvw012-...

# Optional configuration
NOTION_CACHE_DIR=data/notion_cache
NOTION_SCHEMA_CACHE_TTL_HOURS=24
NOTION_DATA_CACHE_TTL_HOURS=6
NOTION_RATE_LIMIT_PER_SEC=3
NOTION_MAX_RELATIONSHIP_DEPTH=1
```

### 3.3 Verify Configuration

```bash
# Test that environment variables are loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', os.getenv('NOTION_API_KEY')[:10] + '...')"
```

---

## Step 4: Basic Usage

### 4.1 Initialize NotionIntegrator

```python
import os
from dotenv import load_dotenv
from src.notion_integrator import NotionIntegrator

# Load environment variables
load_dotenv()

# Initialize integrator
integrator = NotionIntegrator(
    api_key=os.getenv("NOTION_API_KEY"),
    cache_dir=os.getenv("NOTION_CACHE_DIR", "data/notion_cache")
)
```

### 4.2 Fetch All Data (High-Level API)

```python
import asyncio

async def fetch_notion_data():
    # Get all data from both databases
    data = await integrator.get_data(
        companies_db_id=os.getenv("NOTION_DATABASE_ID_COMPANIES"),
        collabiq_db_id=os.getenv("NOTION_DATABASE_ID_COLLABIQ")
    )

    # Print summary
    print(f"Total companies: {data.metadata.total_companies}")
    print(f"Portfolio companies: {data.metadata.portfolio_company_count}")
    print(f"Shinsegae affiliates: {data.metadata.shinsegae_affiliate_count}")
    print(f"Data freshness: {data.metadata.data_freshness}")

    # Access individual companies
    for company in data.companies:
        print(f"- {company.name} ({company.classification.collaboration_type_hint})")

    return data

# Run async function
data = asyncio.run(fetch_notion_data())
```

**Expected output**:
```
Total companies: 123
Portfolio companies: 45
Shinsegae affiliates: 15
Data freshness: fresh
- Company A (PortCo)
- Shinsegae Department Store (SSG)
- Company C (Both)
...
```

### 4.3 Use Formatted Data

```python
# Get Markdown summary for LLM prompt
print(data.summary_markdown)

# Get JSON for programmatic access
import json
print(json.dumps(data.companies[0], indent=2))

# Save to file for later use
with open("notion_companies.json", "w", encoding="utf-8") as f:
    json.dump({
        "companies": [c.__dict__ for c in data.companies],
        "summary": data.summary_markdown,
        "metadata": data.metadata.__dict__
    }, f, indent=2, ensure_ascii=False)
```

---

## Step 5: Advanced Usage

### 5.1 Manual Cache Refresh

```python
# Force fresh fetch (bypass cache)
data = await integrator.get_data(
    companies_db_id=os.getenv("NOTION_DATABASE_ID_COMPANIES"),
    collabiq_db_id=os.getenv("NOTION_DATABASE_ID_COLLABIQ"),
    force_refresh=True
)

# Or refresh specific database
await integrator.refresh_cache(
    database_id=os.getenv("NOTION_DATABASE_ID_COMPANIES"),
    refresh_schema=True,
    refresh_data=True
)
```

### 5.2 Schema Discovery Only

```python
# Discover schema without fetching all data
schema = await integrator.discover_schema(
    database_id=os.getenv("NOTION_DATABASE_ID_COMPANIES")
)

print(f"Database: {schema.database.title}")
print(f"Properties: {schema.property_count}")
print(f"Has relationships: {schema.has_relations}")

# Inspect properties
for prop_name, prop in schema.database.properties.items():
    print(f"- {prop_name}: {prop.type}")
```

### 5.3 Fetch Records with Filters

```python
# Fetch only portfolio companies
records = await integrator.fetch_all_records(
    database_id=os.getenv("NOTION_DATABASE_ID_COMPANIES"),
    filters={
        "property": "Is Portfolio?",
        "checkbox": {"equals": True}
    }
)

print(f"Found {len(records)} portfolio companies")
```

### 5.4 Control Relationship Depth

```python
# Fetch without resolving relationships (faster)
records = await integrator.fetch_all_records(
    database_id=os.getenv("NOTION_DATABASE_ID_COMPANIES"),
    resolve_relationships=False
)

# Or increase relationship depth
integrator = NotionIntegrator(
    api_key=os.getenv("NOTION_API_KEY"),
    max_relationship_depth=2  # Follow relations 2 levels deep
)
```

---

## Step 6: CLI Usage

### 6.1 Add CLI Commands

The NotionIntegrator can be accessed via CLI:

```bash
# Fetch and display company data
uv run collabiq notion fetch

# Refresh cache
uv run collabiq notion refresh --force

# Show schema
uv run collabiq notion schema --database companies

# Export to file
uv run collabiq notion export --output notion_data.json
```

### 6.2 CLI Implementation Example

Add to `src/collabiq/__init__.py`:

```python
import typer
from src.notion_integrator import NotionIntegrator

app = typer.Typer()
notion_app = typer.Typer()
app.add_typer(notion_app, name="notion")

@notion_app.command()
def fetch():
    """Fetch all company data from Notion."""
    import asyncio
    integrator = NotionIntegrator(api_key=os.getenv("NOTION_API_KEY"))
    data = asyncio.run(integrator.get_data(
        companies_db_id=os.getenv("NOTION_DATABASE_ID_COMPANIES"),
        collabiq_db_id=os.getenv("NOTION_DATABASE_ID_COLLABIQ")
    ))
    typer.echo(f"Fetched {data.metadata.total_companies} companies")
    typer.echo(data.summary_markdown)

# ... more commands
```

---

## Step 7: Testing Your Setup

### 7.1 Run Contract Tests

```bash
# Test Notion API integration
pytest tests/contract/test_notion_api_integration.py -v

# Test with real credentials (requires .env setup)
NOTION_API_KEY=secret_... pytest tests/contract/ -v
```

### 7.2 Verify Cache Behavior

```bash
# First run (cache miss, should be slower)
time uv run collabiq notion fetch

# Second run (cache hit, should be fast)
time uv run collabiq notion fetch
```

**Expected timing**:
- First run: 10-60 seconds (depends on database size)
- Second run: <1 second (cache hit)

### 7.3 Inspect Cache Files

```bash
# View cache directory
ls -lh data/notion_cache/

# View schema cache
cat data/notion_cache/schema_companies.json | jq '.'

# View data cache (first 3 records)
cat data/notion_cache/data_companies.json | jq '.content[:3]'

# Check cache age
cat data/notion_cache/data_companies.json | jq '.cached_at, .expires_at'
```

---

## Troubleshooting

### Error: "object not found"

**Cause**: Database not shared with integration

**Solution**:
1. Open database in Notion
2. Click "..." → "Connections" → Connect your integration
3. Try again

### Error: "unauthorized"

**Cause**: Invalid API key or insufficient permissions

**Solution**:
1. Verify API key in `.env` is correct
2. Check integration has "Read content" capability
3. Regenerate integration token if needed

### Error: "rate_limit_exceeded"

**Cause**: Too many requests sent too quickly

**Solution**:
- Reduce `NOTION_RATE_LIMIT_PER_SEC` in `.env`
- Add delay between operations
- Check for bugs causing excessive API calls

### Cache Not Working

**Cause**: Cache directory not writable or corrupted

**Solution**:
```bash
# Check permissions
ls -ld data/notion_cache

# Recreate cache directory
rm -rf data/notion_cache
mkdir -p data/notion_cache

# Force refresh
uv run collabiq notion refresh --force
```

### Unicode Display Issues

**Cause**: Terminal doesn't support UTF-8

**Solution**:
```bash
# Set UTF-8 locale
export LC_ALL=en_US.UTF-8

# Or save to file and view in editor
uv run collabiq notion fetch > output.txt
```

---

## Performance Tips

### 1. Use Cache Effectively

```python
# Set longer TTL for stable data
integrator = NotionIntegrator(
    api_key=os.getenv("NOTION_API_KEY"),
    schema_cache_ttl_hours=48,  # Schema rarely changes
    data_cache_ttl_hours=12      # Data changes more frequently
)
```

### 2. Fetch Only What You Need

```python
# Use filters to reduce data volume
records = await integrator.fetch_all_records(
    database_id=db_id,
    filters={"property": "Status", "select": {"equals": "Active"}},
    max_records=100  # Limit for testing
)
```

### 3. Disable Relationship Resolution for Speed

```python
# Skip relationships if not needed
data = await integrator.fetch_all_records(
    database_id=db_id,
    resolve_relationships=False
)
```

### 4. Monitor Rate Limits

```python
# Check rate limit stats
stats = integrator.get_rate_limit_stats()
print(f"Requests this second: {stats['current_rate']}")
print(f"Queue length: {stats['queue_length']}")
```

---

## Next Steps

After completing this quickstart:

1. **Integration**: Connect NotionIntegrator to your email processing workflow
2. **LLM Integration**: Use formatted data in LLM prompts for company identification
3. **Monitoring**: Set up logging to track cache hits, API calls, and errors
4. **Optimization**: Tune TTL values based on your data update frequency

---

## Example: Complete Workflow

Here's a complete example integrating Notion data into an email processing workflow:

```python
import asyncio
import os
from dotenv import load_dotenv
from src.notion_integrator import NotionIntegrator
from src.llm_integration import LLMProcessor  # Hypothetical

async def process_email_with_notion_context(email_content: str):
    # Load environment
    load_dotenv()

    # Initialize Notion integrator
    notion = NotionIntegrator(api_key=os.getenv("NOTION_API_KEY"))

    # Fetch company data (uses cache if available)
    company_data = await notion.get_data(
        companies_db_id=os.getenv("NOTION_DATABASE_ID_COMPANIES"),
        collabiq_db_id=os.getenv("NOTION_DATABASE_ID_COLLABIQ")
    )

    # Build LLM prompt with company context
    prompt = f"""
# Company Database
{company_data.summary_markdown}

# Email to Analyze
{email_content}

# Task
Identify all companies mentioned in the email and determine:
1. Which companies are involved
2. What type of collaboration this represents (A/B/C/D)
3. Key details about the collaboration

Respond in JSON format.
"""

    # Process with LLM
    llm = LLMProcessor(model="gemini-pro")
    result = llm.process(prompt)

    print(f"Identified companies: {result['companies']}")
    print(f"Collaboration type: {result['collaboration_type']}")

    return result

# Example usage
email = """
Subject: Partnership Opportunity
Company A and Shinsegae Department Store are exploring a strategic partnership...
"""

result = asyncio.run(process_email_with_notion_context(email))
```

---

## Resources

- [Notion API Documentation](https://developers.notion.com/)
- [CollabIQ Architecture](../../docs/ARCHITECTURE.md)
- [Feature Specification](spec.md)
- [API Contracts](contracts/)
- [Data Model](data-model.md)

---

## Support

If you encounter issues:
1. Check [Troubleshooting](#troubleshooting) section above
2. Review logs in `logs/notion_integrator.log`
3. Run with debug logging: `export LOG_LEVEL=DEBUG && uv run collabiq notion fetch`
4. Consult feature specification for expected behavior

**Common Questions**:
- **How often does cache refresh?** Based on TTL (default: 6 hours for data, 24 hours for schema)
- **Can I use multiple Notion workspaces?** Yes, create separate integrations with different API keys
- **What's the rate limit?** 3 requests/second (Notion API limit)
- **Can I export data to CSV?** Yes, write custom formatter or use `jq` to convert JSON
