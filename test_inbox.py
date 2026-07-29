import asyncio
import httpx
from app.main import app

async def run_tests():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        print("Testing /api/inbox/")
        res = await ac.get("/api/inbox/")
        print("GET /api/inbox/:", res.status_code)
        if res.status_code != 200:
            print(res.text)

if __name__ == "__main__":
    asyncio.run(run_tests())
