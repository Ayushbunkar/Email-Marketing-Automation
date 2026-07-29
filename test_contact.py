import asyncio
import httpx

async def test_create_contact():
    payload = {
        "email": "testcontact3@example.com",
        "first_name": "Test",
        "last_name": "Contact",
        "company": "Test Co",
        "lifecycle_stage": "lead"
    }
    
    async with httpx.AsyncClient() as client:
        # Assuming backend is running on 8000
        res = await client.post("http://localhost:8001/contacts/", json=payload)
        print("Status:", res.status_code)
        print("Response:", res.text)

if __name__ == "__main__":
    asyncio.run(test_create_contact())
