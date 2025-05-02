import asyncio
import os
import random
import time
import traceback
from datetime import datetime

import aiohttp
from aiohttp import ClientTimeout
from typing_extensions import List
from web3 import Web3, AsyncWeb3

from CONSTANT import RPC, strLoggingPath, g_ProxyAddress, EnumStatusTask
from Include.Data import DataWallet
from IncludeAsync.AccountEVM import AccountEVM
from Logging import Logging


class AsyncDoTask:
    def __init__(self, pThreadName, pListAccount: List[DataWallet]):
        self.mThreadName = pThreadName
        self.mListAccount = pListAccount
        self.mDictAccTxnNumber = {}
    async def run(self):
        random.shuffle(self.mListAccount)
        await self.HyperlandFarm()

    async def HyperlandFarm(self):
        l_IsAllAccReachTarget = False
        while not l_IsAllAccReachTarget:
            for i in range(0, len(self.mListAccount)):
                self.mListAccount[i].mAddress = Web3.to_checksum_address(self.mListAccount[i].mAddress)
                l_FilePath = os.getcwd() + strLoggingPath.format(
                    str(self.mListAccount[i].mGroup) + "_" + str(self.mListAccount[i].mAddress))
                try:
                    print(f"{self.mThreadName}: Wallet {self.mListAccount[i].mAddress}")

                    if self.mListAccount[i].mAddress not in self.mDictAccTxnNumber:
                        self.mDictAccTxnNumber[self.mListAccount[i].mAddress] = {}
                        self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["IsDone"] = False
                    else:
                        if self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["IsDone"]:
                            continue


                    async with aiohttp.ClientSession() as session:
                        l_Web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC.MONAD_TESTNET_RPC, request_kwargs={'proxy': g_ProxyAddress}))
                        await l_Web3.provider.cache_async_session(session=session)
                        l_Account = AccountEVM(self.mListAccount[i].mPrivateKey, l_Web3, self.mListAccount[i].mGroup)


                        l_ResultTask = await l_RandomTask.DoTask()

                        if l_ResultTask == EnumStatusTask.SUCCESS or l_ResultTask == EnumStatusTask.OUT_OF_BALANCE:
                            self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["IsDone"] = True

                    if len(self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["TasksIsDone"]) \
                        >= self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["TargetTaskAmount"]:
                        self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["IsDone"] = True

                    l_IsAllAccReachTarget = all(wallet["IsDone"] == True for wallet in self.mDictAccTxnNumber.values())
                    await asyncio.sleep(random.randint(2, 4))


                except Exception as e:
                    l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.HyperlandFarm: {type(e).__name__} - {e}\n\n'
                    Logging.WriteLog(l_FilePath, l_TextToLog)
                    print(f"{self.mThreadName}: =>")
                    traceback.print_exc()

            l_RandomSleep = random.randint(900, 1800)
            print(f"{self.mThreadName}: => Sleeping for {l_RandomSleep}s before next round")
            await asyncio.sleep(l_RandomSleep)
            random.shuffle(self.mListAccount)