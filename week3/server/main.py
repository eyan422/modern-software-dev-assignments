"""Rentcast MCP server — exposes Rentcast property data as MCP tools."""

import logging
import os
import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from rentcast import RentcastClient, RentcastError

# Load .env from the week3/ directory (one level up from server/)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# STDIO servers must not write to stdout — log to stderr only
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

mcp = FastMCP("rentcast")


def _client() -> RentcastClient:
    api_key = os.getenv("RENTCAST_API_KEY", "").strip()
    if not api_key:
        raise RentcastError("RENTCAST_API_KEY is not set. Add it to week3/.env.")
    return RentcastClient(api_key)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_rent_estimate(
    address: str,
    property_type: str | None = None,
    bedrooms: int | None = None,
    bathrooms: float | None = None,
    square_footage: int | None = None,
) -> str:
    """Get a monthly rent estimate for a property address.

    Args:
        address: Full street address, e.g. "5500 Grand Lake Dr, San Antonio, TX 78244"
        property_type: One of: Single Family, Condo, Townhouse, Manufactured, Multi Family
        bedrooms: Number of bedrooms
        bathrooms: Number of bathrooms (decimals OK, e.g. 2.5)
        square_footage: Living area in square feet
    """
    try:
        data = await _client().get_rent_estimate(
            address, property_type, bedrooms, bathrooms, square_footage
        )
    except RentcastError as exc:
        return f"Error: {exc}"

    rent = data.get("rent")
    low = data.get("rentRangeLow")
    high = data.get("rentRangeHigh")
    comps = data.get("comparables", [])

    lines = [f"Rent estimate for: {address}"]
    if rent:
        lines.append(f"  Estimated rent:  ${rent:,.0f}/month")
    if low and high:
        lines.append(f"  Range:           ${low:,.0f} – ${high:,.0f}/month")
    if comps:
        lines.append(f"  Comparable rentals used: {len(comps)}")
    if len(lines) == 1:
        lines.append("  No estimate data returned.")

    return "\n".join(lines)


@mcp.tool()
async def get_property_value(
    address: str,
    property_type: str | None = None,
    bedrooms: int | None = None,
    bathrooms: float | None = None,
    square_footage: int | None = None,
) -> str:
    """Get an automated valuation (AVM) estimate for a property.

    Args:
        address: Full street address, e.g. "5500 Grand Lake Dr, San Antonio, TX 78244"
        property_type: One of: Single Family, Condo, Townhouse, Manufactured, Multi Family
        bedrooms: Number of bedrooms
        bathrooms: Number of bathrooms
        square_footage: Living area in square feet
    """
    try:
        data = await _client().get_property_value(
            address, property_type, bedrooms, bathrooms, square_footage
        )
    except RentcastError as exc:
        return f"Error: {exc}"

    price = data.get("price")
    low = data.get("priceRangeLow")
    high = data.get("priceRangeHigh")
    comps = data.get("comparables", [])

    lines = [f"Property value estimate for: {address}"]
    if price:
        lines.append(f"  Estimated value: ${price:,.0f}")
    if low and high:
        lines.append(f"  Range:           ${low:,.0f} – ${high:,.0f}")
    if comps:
        lines.append(f"  Comparable sales used: {len(comps)}")
    if len(lines) == 1:
        lines.append("  No estimate data returned.")

    return "\n".join(lines)


@mcp.tool()
async def search_rental_listings(
    city: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
    bedrooms: int | None = None,
    limit: int = 10,
) -> str:
    """Search active long-term rental listings by location.

    At least one of city, state, or zip_code must be provided.

    Args:
        city: City name, e.g. "Austin"
        state: Two-letter state code, e.g. "TX"
        zip_code: ZIP code, e.g. "78701"
        bedrooms: Filter by exact number of bedrooms
        limit: Max results to return (1–50, default 10)
    """
    if not any([city, state, zip_code]):
        return "Error: Provide at least one of: city, state, or zip_code."

    try:
        data = await _client().search_rental_listings(city, state, zip_code, bedrooms, limit)
    except RentcastError as exc:
        return f"Error: {exc}"

    listings = data if isinstance(data, list) else data.get("data", [])
    if not listings:
        return "No rental listings found for the given criteria."

    lines = [f"Found {len(listings)} rental listing(s):"]
    for i, listing in enumerate(listings, 1):
        addr = listing.get("formattedAddress", "Unknown address")
        rent = listing.get("price")
        beds = listing.get("bedrooms", "?")
        baths = listing.get("bathrooms", "?")
        sqft = listing.get("squareFootage")

        detail = f"{beds}bd/{baths}ba"
        if sqft:
            detail += f", {sqft:,} sqft"
        price_str = f"${rent:,.0f}/mo" if rent else "price unknown"
        lines.append(f"  {i}. {addr} — {price_str} ({detail})")

    return "\n".join(lines)


@mcp.tool()
async def get_market_stats(
    zip_code: str,
    history_range: int = 12,
) -> str:
    """Get rental and sale market statistics for a ZIP code.

    Args:
        zip_code: ZIP code to look up, e.g. "78701"
        history_range: Months of historical data to include (default 12)
    """
    try:
        data = await _client().get_market_stats(zip_code, history_range)
    except RentcastError as exc:
        return f"Error: {exc}"

    lines = [f"Market stats for ZIP {zip_code}:"]

    rental = data.get("rentalData") or {}
    avg_rent = rental.get("averageRent")
    median_rent = rental.get("medianRent")
    total_listings = rental.get("totalListings")
    if avg_rent:
        lines.append(f"  Avg rent:         ${avg_rent:,.0f}/month")
    if median_rent:
        lines.append(f"  Median rent:      ${median_rent:,.0f}/month")
    if total_listings:
        lines.append(f"  Active listings:  {total_listings}")

    sale = data.get("saleData") or {}
    avg_price = sale.get("averagePrice")
    median_price = sale.get("medianPrice")
    if avg_price:
        lines.append(f"  Avg sale price:   ${avg_price:,.0f}")
    if median_price:
        lines.append(f"  Median sale price:${median_price:,.0f}")

    if len(lines) == 1:
        return f"No market data found for ZIP {zip_code}."

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
