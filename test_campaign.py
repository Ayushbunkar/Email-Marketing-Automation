import asyncio
import httpx

async def test_create_campaign():
    payload = {
        "name": "Test Campaign",
        "subject": "Hello World",
        "from_email": "test@example.com",
        "from_name": "Test Sender",
        "content": "This is a test campaign.",
        "type": "broadcast"
    }
    
    async with httpx.AsyncClient() as client:
        # Assuming backend is running on 8000
        res = await client.post("http://localhost:8000/campaigns/", json=payload)
        print("Status:", res.status_code)
        print("Response:", res.text)

if __name__ == "__main__":
    asyncio.run(test_create_campaign())
