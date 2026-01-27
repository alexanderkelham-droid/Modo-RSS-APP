import asyncio
import httpx

API_URL = "https://modo-rss-app-production.up.railway.app/sources/{}"
IDS_TO_ENABLE = [37, 41, 47]  # Financial Times, Power Technology, EIA

async def enable_source(source_id):
    url = API_URL.format(source_id)
    async with httpx.AsyncClient() as client:
        resp = await client.put(url, json={"enabled": True})
        print(f"Source {source_id}: {resp.status_code} {resp.text}")

async def main():
    tasks = [enable_source(i) for i in IDS_TO_ENABLE]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
