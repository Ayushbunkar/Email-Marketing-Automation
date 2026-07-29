import asyncio
from app.db import engine
from sqlalchemy import text

async def main():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [r[0] for r in res]
        print("TABLES IN DB:", tables)

if __name__ == "__main__":
    asyncio.run(main())
