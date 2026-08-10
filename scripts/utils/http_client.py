import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)
HEADERS = {"User-Agent": "tech-radar-bot/1.0 (https://github.com/your-username/tech-radar)"}
MAX_RETRIES = 3
MAX_CONCURRENT_REQUESTS = 20
REQUEST_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


async def get_json(url: str, headers: dict | None = None, params: dict | None = None) -> Any | None:
    merged_headers = {**HEADERS, **(headers or {})}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with REQUEST_SEMAPHORE:
                async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                    response = await client.get(url, headers=merged_headers, params=params)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning("Rate limited on %s, waiting %ds", url, retry_after)
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(retry_after)
                        continue
                    return None
                if response.status_code == 404:
                    logger.warning("404 Not Found: %s", url)
                    return None
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.warning("Timeout on %s (attempt %d/%d)", url, attempt, MAX_RETRIES)
        except httpx.HTTPStatusError as e:
            logger.warning(
                "HTTP error %d on %s (attempt %d/%d)",
                e.response.status_code,
                url,
                attempt,
                MAX_RETRIES,
            )
        except httpx.RequestError as e:
            logger.warning("Request error on %s: %s (attempt %d/%d)", url, e, attempt, MAX_RETRIES)
        if attempt < MAX_RETRIES:
            await asyncio.sleep(2**attempt)
    logger.error("All %d attempts failed for %s", MAX_RETRIES, url)
    return None
