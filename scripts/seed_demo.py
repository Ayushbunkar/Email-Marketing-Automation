"""Seed demo data for Hermes email marketing agent."""

import asyncio
import random
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.db import engine, Base
from app.models.contact import Contact, LifecycleStage, ContactStatus
from app.models.segment import Segment


async def create_demo_contacts(session: AsyncSession) -> None:
    """Create 200 demo contacts across different lifecycle stages and timezones."""
    first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Chris", "Lisa", "James", "Emma"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    companies = ["TechCorp", "MarketingPro", "SalesForce", "GrowthInc", "DataSystems", "CloudSolutions", "WebWorks", "AppDev", "DigitalFirst", "OnlineRetail"]
    timezones = ["Asia/Kolkata", "America/New_York", "Europe/London", "Europe/Paris", "Asia/Tokyo", "Australia/Sydney", "America/Los_Angeles", "Asia/Dubai"]
    
    contacts = []
    for i in range(200):
        lifecycle_stages = [LifecycleStage.LEAD, LifecycleStage.SUBSCRIBER, LifecycleStage.ENGAGED, LifecycleStage.CUSTOMER, LifecycleStage.CHURNED]
        status = ContactStatus.ACTIVE
        
        contact = Contact(
            email=f"user{i+1}@example.com",
            first_name=random.choice(first_names),
            last_name=random.choice(last_names),
            company=random.choice(companies),
            attributes={
                "job_title": random.choice(["Manager", "Director", "VP", "CEO", "CTO", "Developer", "Designer"]),
                "industry": random.choice(["Technology", "Finance", "Healthcare", "Retail", "Manufacturing"]),
                "annual_revenue": random.randint(100000, 10000000),
            },
            lifecycle_stage=random.choice(lifecycle_stages),
            status=status,
            consent_source="demo_import",
            consent_at=datetime.now() - timedelta(days=random.randint(1, 365)),
            timezone=random.choice(timezones),
            last_emailed_at=datetime.now() - timedelta(days=random.randint(1, 30)) if random.random() > 0.5 else None,
        )
        contacts.append(contact)
    
    session.add_all(contacts)
    await session.commit()
    print(f"Created {len(contacts)} demo contacts")


async def create_demo_segment(session: AsyncSession) -> None:
    """Create a demo segment for active leads and subscribers."""
    segment = Segment(
        name="Active Leads & Subscribers",
        description="All active contacts who are leads or subscribers",
        definition={
            "all": [
                {"field": "status", "op": "eq", "value": "active"},
                {"field": "lifecycle_stage", "op": "in", "value": ["lead", "subscriber"]}
            ]
        },
        is_dynamic=True,
        created_by="system",
    )
    session.add(segment)
    await session.commit()
    print("Created demo segment: Active Leads & Subscribers")


async def main() -> None:
    """Main seed function."""
    print("Starting database seed...")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed data
    async with engine.begin() as conn:
        async with AsyncSession(conn) as session:
            await create_demo_contacts(session)
            await create_demo_segment(session)
    
    print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(main())