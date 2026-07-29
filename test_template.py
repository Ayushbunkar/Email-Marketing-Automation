import asyncio
import httpx

async def test_create_template():
    payload = {
        "name": "Test Template",
        "subject": "Hello World",
        "preheader": "Test",
        "body_markdown": "# Test"
    }
    
    async with httpx.AsyncClient() as client:
        # Assuming backend is running on 8000
        res = await client.post("http://localhost:8000/templates/", json=payload)
        print("POST Status:", res.status_code)
        print("POST Response:", res.text)
        
        res = await client.get("http://localhost:8000/templates/")
        print("GET Status:", res.status_code)
        print("GET Response:", res.text)

if __name__ == "__main__":
    asyncio.run(test_create_template())
