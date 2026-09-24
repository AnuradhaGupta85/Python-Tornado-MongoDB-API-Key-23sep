# Seed predefined expense categories in MongoDB.
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv
from database import db, ensure_indexes

load_dotenv('.env_5ad06667-9bcd-48b5-bb6c-a469b3be3571', override=True)

async def seed() -> None:
    await ensure_indexes()
    for name in ['Food', 'Transport', 'Housing', 'Salary']:
        await db.categories.update_one({'name': name, 'is_predefined': True}, {'$setOnInsert': {'name': name, 'user_id': None, 'is_predefined': True, 'created_at': datetime.now(timezone.utc)}}, upsert=True)

if __name__ == '__main__':
    asyncio.run(seed())
