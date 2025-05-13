import asyncio
import decimal
from decimal import Decimal

from eth_typing import ChecksumAddress
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from models import Wallets


class WalletsRepository:
    def __init__(self, pSession: AsyncSession):
        self.mSession = pSession

    async def get_wallet(self, pWalletAddress: ChecksumAddress) -> Wallets | None:
        stmt = select(Wallets).where(Wallets.wallet_address == pWalletAddress)
        result = await self.mSession.execute(stmt)
        return result.scalars().first()

    async def upsert_wallet_stats(self, pWalletAddress: ChecksumAddress,
                                  pFee: decimal.Decimal = 0,
                                  pValue: decimal.Decimal = 0,
                                  pInterchainFee: decimal.Decimal = 0,
                                  pIsComplete: int = 0):
        l_IsIncreaseTxnCount = True if (pFee > 0 and pInterchainFee > 0) else False

        l_stmt = insert(Wallets).values(
            wallet_address=pWalletAddress,
            total_fee=pFee or decimal.Decimal(0),
            total_value=pValue or decimal.Decimal(0),
            total_txn=decimal.Decimal(1),
            total_interchain_fee=pInterchainFee or decimal.Decimal(0),
            is_complete=pIsComplete
        ).on_conflict_do_update(
            index_elements=["wallet_address"],
            set_={
                "total_fee": Wallets.total_fee + pFee,
                "total_value": Wallets.total_value + pValue,
                "total_txn": (Wallets.total_txn + 1) if l_IsIncreaseTxnCount else Wallets.total_txn,
                "total_interchain_fee": Wallets.total_interchain_fee + pInterchainFee,
                "is_complete": pIsComplete
            }
        )
        await self.mSession.execute(l_stmt)
        await self.mSession.commit()

