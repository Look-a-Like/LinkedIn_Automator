import motor.motor_asyncio
from pymongo.errors import ConnectionFailure

# MongoDB connection string - for simplicity using a local MongoDB instance
MONGO_URL = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)

# Database and collections
db = client.job_automation
db.users = client.job_automation.users  # Users collection reference

async def test_connection():
    """Test if MongoDB connection is working."""
    try:
        # The ismaster command is cheap and does not require auth
        await client.admin.command('ismaster')
        return True
    except ConnectionFailure:
        return False