import os
from datetime import datetime

from CONSTANT import strLoggingPath, EnumStatusTask, TokenContract
from IncludeAsync.BaseTask import BaseTask
from Logging import Logging


class TaskTransferToken_MultiToOne(BaseTask):
    def __init__(self, pWeb3, pAccountEVM):
        super().__init__(pWeb3, pAccountEVM)

    async def DoTask(self):
        l_FilePath = os.getcwd() + strLoggingPath.format(
            str(self.mAccountEVM.mGroup) + "_" + str(self.mAccountEVM.GetAddress()))
        l_resultTask = EnumStatusTask.FAILED
        l_IsSuccess = False

        try:
            l_AddressTo = self.mWeb3.to_checksum_address("0x121dd42384db6ad04851f7ac1e81bcd8bbb1876e")
            l_TokenAddress = TokenContract.Base.HYPER
            l_IsSuccess = await self.SendTokenToRootWallet(l_AddressTo, l_TokenAddress)
            l_resultTask = EnumStatusTask.SUCCESS if l_IsSuccess else EnumStatusTask.FAILED

        except Exception as e:
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: TaskTransferToken_MultiToOne.DoTask: {str(e)}\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)

        return l_resultTask