import asyncio
import os
from dotenv import load_dotenv

# Load env before importing app
load_dotenv()

from app.providers.brevo import BrevoProvider
from app.providers.base import SendRequest

async def test_brevo():
    print("Testing Brevo Provider with ACTUAL SEND method...")
    provider = BrevoProvider()
    
    print(f"Using API Key: {provider.api_key[:5]}...{provider.api_key[-5:] if provider.api_key else 'None'}")
    
    req = SendRequest(
        to_email="ayushbunkar636@gmail.com",
        to_name="Ayush Bunkar",
        from_email="marketing@pixelpunch.org",
        from_name="Hermes Admin",
        reply_to="marketing@pixelpunch.org",
        subject="Test from Self-Test Script (FIXED)",
        html="<h1>Hello</h1><p>This is a test</p>",
        text="Hello\nThis is a test",
        headers={},
        idempotency_key="test-12345"
    )
    
    # Actually use the provider.send method to verify the fix
    result = await provider.send(req)
    if result.accepted:
        print("Success! Message ID:", result.provider_message_id)
    else:
        print("Failed!")
        print("Error:", result.error)
        
    # Also let's test create_marketing_campaign
    print("Testing Marketing Campaign creation...")
    camp_result = await provider.create_marketing_campaign(
        name="Test Campaign API",
        subject="Test Campaign Subject",
        html_content="<h1>API Test</h1>",
        sender_email="marketing@pixelpunch.org",
        sender_name="Hermes Admin"
    )
    print(camp_result)
        
    await provider.close()

if __name__ == "__main__":
    asyncio.run(test_brevo())
