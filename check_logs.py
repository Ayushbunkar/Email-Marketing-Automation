import asyncio
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

async def check_logs():
    api_key = os.getenv("BREVO_API_KEY")
    if not api_key:
        print("No BREVO_API_KEY found")
        return
        
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.brevo.com/v3/smtp/statistics/events",
            headers={
                "api-key": api_key,
                "Content-Type": "application/json"
            },
            params={"limit": 5, "sort": "desc"}
        )
        print("Status:", response.status_code)
        
        try:
            data = response.json()
            events = data.get("events", [])
            print(f"Found {len(events)} recent events:")
            for e in events:
                print(f"- {e.get('date')} | {e.get('event')} | To: {e.get('email')} | MsgID: {e.get('messageId')}")
        except Exception as ex:
            print("Error parsing:", ex)
            print("Raw response:", response.text)

if __name__ == "__main__":
    asyncio.run(check_logs())
