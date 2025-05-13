from typing import List, Optional

from sqlalchemy import DateTime, ForeignKeyConstraint, Index, Integer, Numeric, PrimaryKeyConstraint, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime
import decimal

class Base(DeclarativeBase):
    pass


class ChainExplorers(Base):
    __tablename__ = 'chain_explorers'
    __table_args__ = (
        PrimaryKeyConstraint('chain_id', name='chain_explorers_pkey'),
    )

    chain_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    explorer_url: Mapped[Optional[str]] = mapped_column(String(100))

    transactions: Mapped[List['Transactions']] = relationship('Transactions', back_populates='chain')


class Wallets(Base):
    __tablename__ = 'wallets'
    __table_args__ = (
        PrimaryKeyConstraint('wallet_address', name='wallets_pkey'),
    )

    wallet_address: Mapped[str] = mapped_column(String(100), primary_key=True)
    total_fee: Mapped[decimal.Decimal] = mapped_column(Numeric(38, 18), server_default=text('0'))
    total_value: Mapped[decimal.Decimal] = mapped_column(Numeric(38, 18), server_default=text('0'))
    total_txn: Mapped[decimal.Decimal] = mapped_column(Numeric(38, 18), server_default=text('0'))
    total_interchain_fee: Mapped[decimal.Decimal] = mapped_column(Numeric(38, 18), server_default=text('0'))
    is_complete: Mapped[decimal.Decimal] = mapped_column(Numeric, server_default=text('0'))

    transactions: Mapped[List['Transactions']] = relationship('Transactions', back_populates='wallets')


class Transactions(Base):
    __tablename__ = 'transactions'
    __table_args__ = (
        ForeignKeyConstraint(['chain_id'], ['chain_explorers.chain_id'], name='transactions_chain_explorer_fkey'),
        ForeignKeyConstraint(['wallet_address'], ['wallets.wallet_address'], name='transactions_wallet_address_fkey'),
        PrimaryKeyConstraint('txn_hash', name='transactions_pkey'),
        Index('fki_transactions_chain_explorer_fkey', 'chain_id')
    )

    txn_hash: Mapped[str] = mapped_column(String(100), primary_key=True)
    wallet_address: Mapped[str] = mapped_column(String(100))
    txn_fee: Mapped[decimal.Decimal] = mapped_column(Numeric(38, 18))
    txn_value: Mapped[decimal.Decimal] = mapped_column(Numeric(38, 18))
    txn_date: Mapped[datetime.datetime] = mapped_column(DateTime)
    interchain_fee: Mapped[decimal.Decimal] = mapped_column(Numeric(38, 18))
    chain_id: Mapped[int] = mapped_column(Integer)

    chain: Mapped['ChainExplorers'] = relationship('ChainExplorers', back_populates='transactions')
    wallets: Mapped['Wallets'] = relationship('Wallets', back_populates='transactions')
