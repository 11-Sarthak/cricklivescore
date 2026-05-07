print("SCRIPT STARTED")

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("IMPORTS DONE")

from app.db import create_db_and_tables

print("DB IMPORT DONE")


async def main():
    print("Creating DB...")
    await create_db_and_tables()
    print("Done")


print("RUNNING ASYNC")

asyncio.run(main())