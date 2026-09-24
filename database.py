# MongoDB connection configuration for the expense tracker.
import os
from dotenv import load_dotenv
from motor.motor_tornado import MotorClient

load_dotenv('.env_5ad06667-9bcd-48b5-bb6c-a469b3be3571', override=True)
DATABASE_URL = os.getenv('DATABASE_URL', 'mongodb://localhost:27017/gen_476aba8b5f9e')
DATABASE_NAME = DATABASE_URL.rsplit('/', 1)[-1].split('?', 1)[0] or 'gen_476aba8b5f9e'
client = MotorClient(DATABASE_URL, serverSelectionTimeoutMS=5000)
db = client[DATABASE_NAME]

async def ensure_indexes() -> None:
    await db.users.create_index('email', unique=True)
    await db.api_keys.create_index('key_hash', unique=True)
    await db.transactions.create_index([('user_id', 1), ('date', -1)])
    await db.categories.create_index([('user_id', 1), ('name', 1)], unique=True, partialFilterExpression={'user_id': {'$type': 'string'}})
    for name in ['Food', 'Transport', 'Housing', 'Salary']:
        await db.categories.update_one({'name': name, 'is_predefined': True}, {'$setOnInsert': {'name': name, 'user_id': None, 'is_predefined': True}}, upsert=True)
