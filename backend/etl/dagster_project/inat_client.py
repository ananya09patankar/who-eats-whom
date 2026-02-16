import httpx
INAT_BASE = "https://api.inaturalist.org/v1"

async def fetch_observations(page: int, per_page: int = 200, **params) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{INAT_BASE}/observations", params={"page": page, "per_page": per_page, **params})
        r.raise_for_status()
        return r.json()
