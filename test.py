# main.py
import asyncio

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from IncludeAsync.Database.AsyncPostgresClient import AsyncPostgresClient
from models import ChainExplorers, Wallets, Transactions

DB_URL = "postgresql+asyncpg://postgres:long123@167.86.105.4:5432/HyperlandFarm"


async def main():
    db = AsyncPostgresClient(DB_URL)

    async for session in db.get_session():
        l_query = select(Wallets)\
            .options(joinedload(Wallets.transactions)) \
            .where(Wallets.wallet_address == '0x8e7f51b185c5E16759a444bA7B4365711f4daf7d')
        stmt = (
            select(Wallets)
            .options(joinedload(Wallets.transactions))
            .where(Wallets.wallet_address == '0x8e7f51b185c5E16759a444bA7B4365711f4daf7d')
        )
        result = await session.execute(stmt)
        wallet = result.scalars().first()
        for tx in wallet.transactions:
            print(tx.txn_hash, tx.txn_value)

asyncio.run(main())
