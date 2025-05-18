import os
from datetime import datetime

from CONSTANT import strLoggingPath, gDictChainID, RPC, TokenContract
from IncludeAsync.AccountEVM import AccountEVM
from IncludeAsync.Database.AsyncPostgresClient import AsyncPostgresClient
from Logging import Logging
from Tasks.TaskBridgeToken import TaskBridgeToken
from web3 import AsyncWeb3


class TaskBridgeHYPER(TaskBridgeToken):
    def __init__(self, pWeb3, pAccountEVM: AccountEVM, pDatabaseConn: AsyncPostgresClient):
        super().__init__(pWeb3, pAccountEVM, pDatabaseConn)

    async def Get_Token_Address(self, pChainID):
        l_FilePath = os.getcwd() + strLoggingPath.format(
            str(self.mAccountEVM.mGroup) + "_" + str(self.mAccountEVM.GetAddress()))
        try:
            chain_mapping = {
                gDictChainID[RPC.BSC_RPC]["chainID"]: TokenContract.BSC.HYPER,
            }
            if pChainID in chain_mapping:
                return chain_mapping[pChainID]
            raise Exception("ChainID not supported")
        except Exception as e:
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: {self.__class__.__name__}.Get_Token_Address: {type(e).__name__} - {e}\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)