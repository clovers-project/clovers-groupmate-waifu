import httpx
import asyncio

_client: httpx.AsyncClient


async def utils_startup():
    global _client
    _client = httpx.AsyncClient()


async def utils_shutdown():
    await _client.aclose()


async def download_url(url: str, retry: int = 3):
    async def retry_download(url: str, retry: int):
        for _ in range(retry):
            try:
                resp = await _client.get(url, timeout=20)
                resp.raise_for_status()
                return resp.content
            except httpx.HTTPStatusError:
                await asyncio.sleep(3)

    return await retry_download(url, retry)


def download_urls(urls: list[str]):
    return asyncio.gather(*map(download_url, urls))
