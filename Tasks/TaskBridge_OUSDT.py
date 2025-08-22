import os
from datetime import datetime

import aiohttp

from CONSTANT import strLoggingPath, gDictChainID, RPC, TokenContract, g_ProxyAddress
from IncludeAsync.AccountEVM import AccountEVM
from IncludeAsync.Database.AsyncPostgresClient import AsyncPostgresClient
from Logging import Logging
from Tasks.TaskBridgeToken import TaskBridgeToken
from web3 import AsyncWeb3


class TaskBridge_OUSDT(TaskBridgeToken):
    def __init__(self, pWeb3, pAccountEVM: AccountEVM, pDatabaseConn: AsyncPostgresClient):
        super().__init__(pWeb3, pAccountEVM, pDatabaseConn)

    async def Get_Token_Address(self, pChainID):
        l_FilePath = os.getcwd() + strLoggingPath.format(
            str(self.mAccountEVM.mGroup) + "_" + str(self.mAccountEVM.GetAddress()))
        try:
            chain_mapping = {
                gDictChainID[RPC.OP_RPC]["chainID"]: TokenContract.OP.OUSDT,
                gDictChainID[RPC.BASE_RPC]["chainID"]: TokenContract.Base.OUSDT,
            }
            if pChainID in chain_mapping:
                return chain_mapping[pChainID]
            raise Exception("ChainID not supported")
        except Exception as e:
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: {self.__class__.__name__}.Get_Token_Address: {type(e).__name__} - {e}\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)


async def main():
    strRPCNode = RPC.BASE_RPC
    async with aiohttp.ClientSession() as session:
        l_web3 = AsyncWeb3(
            AsyncWeb3.AsyncHTTPProvider(strRPCNode, request_kwargs={'proxy': g_ProxyAddress}))
        await l_web3.provider.cache_async_session(session=session)

        l_AccoutnEVM = AccountEVM("0xba804ce3d5cc7ec7b7bfb145bb9331a853d0dd7983fc5c9280d6f770ebbc296b", l_web3)

        username = "longdoan"
        password = "long123456"
        ip = "173.249.39.80"
        DB_name = "hyperlandfarm"
        DB_URL = f"postgresql+asyncpg://{username}:{password}@{ip}:5432/{DB_name}"
        l_db = AsyncPostgresClient(DB_URL)

        l_Task = TaskBridge_OUSDT(l_web3, l_AccoutnEVM, l_db)
        l_txn = await l_Task.DoTask(8453, 10, 50)


        print(l_txn)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())