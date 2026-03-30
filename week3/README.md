# Week 3 — Rentcast MCP Server

An MCP server that wraps the [Rentcast API](https://rentcast.io) to expose real-estate data
(rent estimates, property valuations, rental listings, and market stats) as tools callable by
Claude Desktop or any MCP-aware client.

## Prerequisites

- Python 3.10+
- A free [Rentcast API key](https://app.rentcast.io/app/api) (50 requests/month on the free tier)
- Dependencies installed via Poetry (see root `pyproject.toml`)

## Setup

```bash
# From the repo root
conda activate cs146s        # or your Python env
poetry install --no-interaction

# Create your .env file
cp week3/.env.example week3/.env
# Edit week3/.env and paste your Rentcast API key
```

## Running the server

```bash
# From the repo root
python week3/server/main.py
```

The server speaks MCP over **STDIO** — you don't interact with it directly. Configure a client
(see below) and the client launches it for you.

## Claude Desktop configuration

Add the following to your Claude Desktop config
(`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "rentcast": {
      "command": "/absolute/path/to/your/python",
      "args": ["/absolute/path/to/week3/server/main.py"],
      "env": {
        "RENTCAST_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

> **Important:** Claude Desktop launches processes with a minimal PATH that won't include conda
> or Poetry virtualenvs. Use the **absolute path** to the Python binary, not just `python`.
>
> Find your Python path:
> ```bash
> # Poetry virtualenv (this project)
> poetry run which python
> # or conda
> conda run -n cs146s which python
> ```

Restart Claude Desktop after editing the config. You should see **rentcast** listed under
"Connected MCP Servers" in the app.

## Debugging with MCP Inspector

```bash
npx @modelcontextprotocol/inspector python week3/server/main.py
```

Open the Inspector URL in your browser to call tools interactively without Claude Desktop.

## Tool reference

### `get_rent_estimate`

Get a monthly rent estimate for a property.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `address` | string | yes | Full street address, e.g. `"5500 Grand Lake Dr, San Antonio, TX 78244"` |
| `property_type` | string | no | `Single Family`, `Condo`, `Townhouse`, `Manufactured`, `Multi Family` |
| `bedrooms` | integer | no | Number of bedrooms |
| `bathrooms` | float | no | Number of bathrooms (e.g. `2.5`) |
| `square_footage` | integer | no | Living area in sq ft |

**Example output:**
```
Rent estimate for: 5500 Grand Lake Dr, San Antonio, TX 78244
  Estimated rent:  $1,450/month
  Range:           $1,200 – $1,700/month
  Comparable rentals used: 8
```

---

### `get_property_value`

Get an automated valuation (AVM) estimate for a property.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `address` | string | yes | Full street address |
| `property_type` | string | no | Same options as above |
| `bedrooms` | integer | no | Number of bedrooms |
| `bathrooms` | float | no | Number of bathrooms |
| `square_footage` | integer | no | Living area in sq ft |

**Example output:**
```
Property value estimate for: 5500 Grand Lake Dr, San Antonio, TX 78244
  Estimated value: $215,000
  Range:           $195,000 – $235,000
  Comparable sales used: 5
```

---

### `search_rental_listings`

Search active long-term rental listings by location. At least one of `city`, `state`, or
`zip_code` is required.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `city` | string | no | City name, e.g. `"Austin"` |
| `state` | string | no | Two-letter state code, e.g. `"TX"` |
| `zip_code` | string | no | ZIP code, e.g. `"78701"` |
| `bedrooms` | integer | no | Filter by exact bedroom count |
| `limit` | integer | no | Max results (1–50, default 10) |

**Example output:**
```
Found 3 rental listing(s):
  1. 123 Main St, Austin, TX 78701 — $2,100/mo (2bd/2.0ba, 950 sqft)
  2. 456 Elm Ave, Austin, TX 78702 — $1,850/mo (2bd/1.0ba, 820 sqft)
  3. 789 Oak Blvd, Austin, TX 78703 — $2,400/mo (2bd/2.0ba, 1,050 sqft)
```

---

### `get_market_stats`

Get rental and sale market statistics for a ZIP code.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `zip_code` | string | yes | ZIP code, e.g. `"78701"` |
| `history_range` | integer | no | Months of history to include (default 12) |

**Example output:**
```
Market stats for ZIP 78701:
  Avg rent:         $2,350/month
  Median rent:      $2,200/month
  Active listings:  47
  Avg sale price:   $485,000
  Median sale price:$460,000
```

## Example invocation flow (Claude Desktop)

1. Open Claude Desktop and start a new conversation.
2. Ask: *"What's the estimated rent for 5500 Grand Lake Dr, San Antonio, TX 78244?"*
3. Claude calls `get_rent_estimate` and returns the result.
4. Follow up: *"And what's the market like in ZIP 78244?"*
5. Claude calls `get_market_stats` with `zip_code="78244"`.

## Rate limits

The Rentcast free tier allows **50 requests/month**. If you exceed this, the server returns a
clear error message rather than crashing. Upgrade your plan at rentcast.io for higher limits.

## Project structure

```
week3/
  server/
    main.py       # FastMCP server — tool definitions and entrypoint
    rentcast.py   # Async httpx client wrapping the Rentcast REST API
  .env.example    # Template for environment variables
  .env            # Your secrets (git-ignored)
  README.md       # This file
```