import asyncio
from database.db import init_db, activate_pro


USER_ID = 916037494


async def main():
    await init_db()
    await activate_pro(USER_ID, days=30)
    print("PRO activated for user:", USER_ID)


if __name__ == "__main__":
    asyncio.run(main())