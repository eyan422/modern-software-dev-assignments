"""Async HTTP client for the Rentcast API."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.rentcast.io/v1"
TIMEOUT = 10.0


class RentcastError(Exception):
    """Raised for all Rentcast API errors."""


class RentcastClient:
    def __init__(self, api_key: str) -> None:
        self._headers = {"X-Api-Key": api_key, "Accept": "application/json"}

    async def _get(self, path: str, params: dict[str, Any]) -> Any:
        clean = {k: v for k, v in params.items() if v is not None}
        url = f"{BASE_URL}{path}"
        logger.info("GET %s params=%s", url, clean)

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            try:
                resp = await client.get(url, headers=self._headers, params=clean)
            except httpx.TimeoutException:
                raise RentcastError("Request timed out. Rentcast API may be slow — try again.")
            except httpx.RequestError as exc:
                raise RentcastError(f"Network error: {exc}")

        if resp.status_code == 401:
            raise RentcastError("Invalid API key. Check your RENTCAST_API_KEY.")
        if resp.status_code == 404:
            raise RentcastError("No data found for the given parameters.")
        if resp.status_code == 429:
            raise RentcastError(
                "Rate limit exceeded. The Rentcast free tier allows 50 requests/month. "
                "Please wait before retrying."
            )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RentcastError(f"HTTP {exc.response.status_code}: {exc.response.text[:200]}")

        return resp.json()

    async def get_rent_estimate(
        self,
        address: str,
        property_type: str | None = None,
        bedrooms: int | None = None,
        bathrooms: float | None = None,
        square_footage: int | None = None,
    ) -> dict[str, Any]:
        return await self._get(
            "/avm/rent/long-term",
            {
                "address": address,
                "propertyType": property_type,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "squareFootage": square_footage,
            },
        )

    async def get_property_value(
        self,
        address: str,
        property_type: str | None = None,
        bedrooms: int | None = None,
        bathrooms: float | None = None,
        square_footage: int | None = None,
    ) -> dict[str, Any]:
        return await self._get(
            "/avm/value",
            {
                "address": address,
                "propertyType": property_type,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "squareFootage": square_footage,
            },
        )

    async def search_rental_listings(
        self,
        city: str | None = None,
        state: str | None = None,
        zip_code: str | None = None,
        bedrooms: int | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return await self._get(
            "/listings/rental/long-term",
            {
                "city": city,
                "state": state,
                "zipCode": zip_code,
                "bedrooms": bedrooms,
                "limit": min(limit, 50),
            },
        )

    async def get_market_stats(
        self,
        zip_code: str,
        history_range: int = 12,
    ) -> dict[str, Any]:
        return await self._get(
            "/markets",
            {
                "zipCode": zip_code,
                "historyRange": history_range,
            },
        )
