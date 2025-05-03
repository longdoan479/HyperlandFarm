import decimal
import os
import random
from datetime import datetime

import aiohttp
from web3 import AsyncWeb3

from CONSTANT import strLoggingPath, EnumStatusTask, RPC, g_ProxyAddress
from IncludeAsync.AccountEVM import AccountEVM
from IncludeAsync.Bridge.UseNexus import UseNexus
from IncludeAsync.ConnectWeb3 import ConnectWeb3
from IncludeAsync.Database.AsyncPostgresClient import AsyncPostgresClient
from Logging import Logging
from Repository.TransactionsRepository import TransactionRepository
from Repository.WalletsRepository import WalletsRepository


class TaskBridgeETH_UseNexus(ConnectWeb3):
    def __init__(self, pWeb3: AsyncWeb3, pAccountEVM: AccountEVM, pDatabaseConn: AsyncPostgresClient):
        super().__init__(pWeb3)
        self.mAccountEVM = pAccountEVM
        self.mDatabaseConn = pDatabaseConn

    async def DoTask(self, pChainID_From: int, pChainID_To: int):
        l_FilePath = os.getcwd() + strLoggingPath.format(
            str(self.mAccountEVM.mGroup) + "_" + str(self.mAccountEVM.GetAddress()))
        l_resultTask = EnumStatusTask.FAILED

        try:
            l_GasPrice = await self.mWeb3.eth.gas_price

            l_UseNexus = UseNexus(self.mWeb3, self.mAccountEVM)
            l_BalanceETH = float(self.mWeb3.from_wei(await self.mAccountEVM.GetBalanceETH(), "ether"))
            l_AmountToBridge = round((l_BalanceETH - 0.0004) / (random.uniform(1.04, 1.06)),
                                     random.randint(5,7))

            l_TxnBridge, l_IsSuccessTXN, l_QuoteGasPayment, l_TxnFee = await l_UseNexus.BridgeETH(
                l_AmountToBridge,
                pChainID_To,
                self.mAccountEVM.GetAddress(),
                l_GasPrice,
            )

            if l_IsSuccessTXN:
                async for session in self.mDatabaseConn.get_session():
                    l_WalletsRepo = WalletsRepository(session)
                    await l_WalletsRepo.upsert_wallet_stats(self.mAccountEVM.GetAddress(),
                                                                self.mWeb3.from_wei(l_TxnFee, "ether"),
                                                                decimal.Decimal(l_AmountToBridge),
                                                                self.mWeb3.from_wei(l_QuoteGasPayment, "ether"))

                    l_TransactionRepo = TransactionRepository(session)
                    await l_TransactionRepo.upsert_transaction_stats(l_TxnBridge,
                                                                    self.mAccountEVM.GetAddress(),
                                                                     self.mWeb3.from_wei(l_GasPrice, "ether"),
                                                                     decimal.Decimal(l_AmountToBridge),
                                                                     self.mWeb3.from_wei(l_QuoteGasPayment, "ether"),
                                                                     await self.GetChainID())

                l_TextToLog = f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: TaskBridgeETH_UseNexus - Account {self.mAccountEVM.GetAddress()}:' \
                              f'\n => Bridge from {pChainID_From} to {pChainID_To}\n' \
                              f'\n => {str(l_TxnBridge)}\n'
                Logging.WriteLog(l_FilePath, l_TextToLog)
                l_resultTask = EnumStatusTask.SUCCESS
            else:
                l_TextToLog = f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: TaskBridgeETH_UseNexus - Account {self.mAccountEVM.GetAddress()}:' \
                              f'\n => Bridge from {pChainID_From} to {pChainID_To}\n' \
                              f'\n => Failed \n'
                Logging.WriteLog(l_FilePath, l_TextToLog)
        except Exception as e:
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: TaskBridgeETH_UseNexus: {type(e).__name__} - {e}\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)

        return l_resultTask

DB_URL = "postgresql+asyncpg://postgres:long123@localhost/HyperlandFarm"


async def main():
    strRPCNode = RPC.OP_RPC
    db = AsyncPostgresClient(DB_URL)

    async with aiohttp.ClientSession() as session:
        l_web3 = AsyncWeb3(
            AsyncWeb3.AsyncHTTPProvider(strRPCNode, request_kwargs={'proxy': g_ProxyAddress}))
        await l_web3.provider.cache_async_session(session=session)

        l_AccoutnEVM = AccountEVM("", l_web3)

        l_Task = TaskBridgeETH_UseNexus(l_web3, l_AccoutnEVM, db)
        l_txn, l_IsSuccess, l_GasPayout = await l_Task.DoTask(10, 56)


        print(l_txn, l_IsSuccess)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())