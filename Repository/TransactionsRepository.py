import decimal
from datetime import datetime

from eth_typing import ChecksumAddress
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from models import Transactions


class TransactionRepository:
    def __init__(self, pSession: AsyncSession):
        self.mSession = pSession

    async def get_transaction(self, pTxnHash: str) -> Transactions | None:
        stmt = select(Transactions).where(Transactions.txn_hash == pTxnHash)
        result = await self.mSession.execute(stmt)
        return result.scalars().first()

    async def upsert_transaction_stats(self, pTxnHash: str, pWalletAddress: ChecksumAddress, pFee: decimal.Decimal, pValue: decimal.Decimal, pInterchainFee: decimal.Decimal, pChainID: int):
        l_stmt = insert(Transactions).values(
            txn_hash=pTxnHash,
            wallet_address=pWalletAddress,
            txn_fee=pFee or decimal.Decimal(0),
            txn_value=pValue or decimal.Decimal(0),
            txn_date=datetime.now(),
            interchain_fee=pInterchainFee or decimal.Decimal(0),
            chain_id=pChainID,
        ).on_conflict_do_update(
            index_elements=["txn_hash"],
            set_={
                "txn_fee": pFee or decimal.Decimal(0),
                "txn_value": pValue or decimal.Decimal(0),
                "interchain_fee": pInterchainFee or decimal.Decimal(0)
            }
        )
        await self.mSession.execute(l_stmt)
        await self.mSession.commit()