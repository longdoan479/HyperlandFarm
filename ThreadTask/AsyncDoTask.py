import asyncio
import os
import random
import time
import traceback
from datetime import datetime

import aiohttp
from aiohttp import ClientTimeout
from eth_typing import ChecksumAddress
from typing_extensions import List
from web3 import Web3, AsyncWeb3

from CONSTANT import RPC, strLoggingPath, g_ProxyAddress, EnumStatusTask, gDictChainID, TokenContract, gDictTokenDecimal
from Include.Data import DataWallet
from IncludeAsync.AccountEVM import AccountEVM
from IncludeAsync.Database.AsyncPostgresClient import AsyncPostgresClient
from IncludeAsync.TokenERC20.TokenERC20 import TokenERC20
from Logging import Logging
from Repository.WalletsRepository import WalletsRepository
from Tasks.TaskBridgeETH_UseNexus import TaskBridgeETH_UseNexus
from Tasks.TaskBridgeEnzoETH import TaskBridgeEnzoETH


class AsyncDoTask:
    def __init__(self, pThreadName, pListAccount: List[DataWallet], pDatabaseConn: AsyncPostgresClient):
        self.mThreadName = pThreadName
        self.mListAccount = pListAccount
        self.mDictAccTxnNumber = {}
        self.mDatabaseConn = pDatabaseConn

    async def run(self):
        random.shuffle(self.mListAccount)
        # await self.HyperlandFarm_BridgeETH()
        await self.HyperlandFarm_Bridge_renzoETH()

    async def HyperlandFarm_BridgeETH(self):
        l_IsAllAccReachTarget = False
        while not l_IsAllAccReachTarget:
            for i in range(0, len(self.mListAccount)):
                self.mListAccount[i].mAddress = Web3.to_checksum_address(self.mListAccount[i].mAddress)
                l_FilePath = os.getcwd() + strLoggingPath.format(
                    str(self.mListAccount[i].mGroup) + "_" + str(self.mListAccount[i].mAddress))
                try:
                    l_RPC_From = await self.GetChainHaveBalance(self.mListAccount[i])

                    if l_RPC_From == "" or l_RPC_From is None:
                        continue
                    print(f"{self.mThreadName}: Wallet {self.mListAccount[i].mAddress}, RPC {l_RPC_From}")

                    l_DataWallet = await self.GetDataWallet(self.mListAccount[i].mAddress)

                    if self.mListAccount[i].mAddress not in self.mDictAccTxnNumber:
                        l_RandomTarget = random.randint(20, 25)

                        self.mDictAccTxnNumber[self.mListAccount[i].mAddress] = {}
                        self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["TargetTxnAmount"] = l_RandomTarget
                        self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["IsDone"] = False if l_DataWallet is None or l_RandomTarget > l_DataWallet.total_txn else True
                    else:
                        if self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["IsDone"]:
                            continue
                        else:
                            if l_DataWallet is None or \
                            self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["TargetTxnAmount"] > l_DataWallet.total_txn:
                                self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["IsDone"] = False
                            else:
                                self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["IsDone"] = True
                                continue

                    l_RoutePath = [
                        RPC.OP_RPC,
                        RPC.ARB_RPC,
                        RPC.BASE_RPC,
                    ]
                    l_RoutePath = [l_rpc for l_rpc in l_RoutePath if l_rpc != l_RPC_From]
                    l_RPC_To = random.choice(l_RoutePath)

                    l_ChainID_From = gDictChainID[l_RPC_From]["chainID"]
                    l_ChainID_To = gDictChainID[l_RPC_To]["chainID"]
                    async with aiohttp.ClientSession() as session:
                        l_Web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(l_RPC_From, request_kwargs={'proxy': g_ProxyAddress}))
                        await l_Web3.provider.cache_async_session(session=session)
                        l_Account = AccountEVM(self.mListAccount[i].mPrivateKey, l_Web3, self.mListAccount[i].mGroup)

                        l_TaskBridgeETH_UseNexus = TaskBridgeETH_UseNexus(l_Web3, l_Account, self.mDatabaseConn)
                        l_ResultTask = await l_TaskBridgeETH_UseNexus.DoTask(l_ChainID_From, l_ChainID_To)



                    l_IsAllAccReachTarget = all(wallet["IsDone"] == True for wallet in self.mDictAccTxnNumber.values())
                    await asyncio.sleep(random.randint(20, 80))


                except Exception as e:
                    l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.HyperlandFarm: {type(e).__name__} - {e}\n\n'
                    Logging.WriteLog(l_FilePath, l_TextToLog)
                    print(f"{self.mThreadName}: =>")
                    traceback.print_exc()

            l_RandomSleep = random.randint(900, 1800)
            print(f"{self.mThreadName}: => Sleeping for {l_RandomSleep}s before next round")
            await asyncio.sleep(l_RandomSleep)
            random.shuffle(self.mListAccount)

    async def HyperlandFarm_Bridge_renzoETH(self):
        l_IsAllAccReachTarget = False
        while not l_IsAllAccReachTarget:
            for i in range(0, len(self.mListAccount)):
                self.mListAccount[i].mAddress = Web3.to_checksum_address(self.mListAccount[i].mAddress)
                l_FilePath = os.getcwd() + strLoggingPath.format(
                    str(self.mListAccount[i].mGroup) + "_" + str(self.mListAccount[i].mAddress))
                try:
                    l_RPC_From = await self.GetChainHaveETH_and_renzoETH(self.mListAccount[i])

                    if l_RPC_From == "" or l_RPC_From is None:
                        continue
                    print(f"{self.mThreadName}: Wallet {self.mListAccount[i].mAddress}, RPC {l_RPC_From}")

                    l_DataWallet = await self.GetDataWallet(self.mListAccount[i].mAddress)

                    l_wallet_entry = self.mDictAccTxnNumber.get(self.mListAccount[i].mAddress)

                    # Check if wallet exists in dictionary
                    if l_wallet_entry is None:
                        # Initialize new wallet entry
                        l_RandomTarget = random.randint(7, 9)
                        l_is_complete = False if l_DataWallet is None or l_DataWallet.is_complete == 0 else True
                        self.mDictAccTxnNumber[self.mListAccount[i].mAddress] = {
                            "TargetTxnAmount": l_RandomTarget,
                            "IsDone": l_is_complete
                        }

                        if l_is_complete:
                            continue
                    else:
                        # Skip if wallet is already marked as done
                        if l_wallet_entry["IsDone"]:
                            continue

                        # Update IsDone status based on wallet data
                        if l_DataWallet is not None and l_DataWallet.is_complete == 1:
                            l_wallet_entry["IsDone"] = True
                            continue

                    l_RoutePath = [
                        RPC.OP_RPC,
                        RPC.ARB_RPC,
                        RPC.BASE_RPC,
                    ]
                    l_RoutePath = [l_rpc for l_rpc in l_RoutePath if l_rpc != l_RPC_From]
                    l_RPC_HaveBalance = await self.GetChainHaveBalance_FromListRPC(self.mListAccount[i], l_RoutePath, 0.001)

                    if len(l_RPC_HaveBalance) > 0:
                        l_RPC_To = random.choice(l_RPC_HaveBalance)

                        l_ChainID_From = gDictChainID[l_RPC_From]["chainID"]
                        l_ChainID_To = gDictChainID[l_RPC_To]["chainID"]
                        async with aiohttp.ClientSession() as session:
                            l_Web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(l_RPC_From, request_kwargs={'proxy': g_ProxyAddress}))
                            await l_Web3.provider.cache_async_session(session=session)
                            l_Account = AccountEVM(self.mListAccount[i].mPrivateKey, l_Web3, self.mListAccount[i].mGroup)

                            l_TaskBridgeToken_UseNexus = TaskBridgeEnzoETH(l_Web3, l_Account, self.mDatabaseConn)
                            l_ResultTask = await l_TaskBridgeToken_UseNexus.DoTask(l_ChainID_From, l_ChainID_To)

                            if l_ResultTask == EnumStatusTask.SUCCESS:
                                l_DataWallet = await self.GetDataWallet(self.mListAccount[i].mAddress)

                                if l_DataWallet is not None and self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["TargetTxnAmount"] <= l_DataWallet.total_txn:
                                    await self.Update_IsComplete_Data_Wallet(self.mListAccount[i].mAddress)

                        l_IsAllAccReachTarget = all(wallet["IsDone"] == True for wallet in self.mDictAccTxnNumber.values())
                        await asyncio.sleep(random.randint(100, 300))

                except Exception as e:
                    l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.HyperlandFarm_Bridge_renzoETH: {type(e).__name__} - {e}\n\n'
                    Logging.WriteLog(l_FilePath, l_TextToLog)
                    print(f"{self.mThreadName}: =>")
                    traceback.print_exc()

            l_RandomSleep = random.randint(500, 3000)
            print(f"{self.mThreadName}: => Sleeping for {l_RandomSleep}s before next round")
            await asyncio.sleep(l_RandomSleep)
            random.shuffle(self.mListAccount)

    async def GetChainHaveBalance(self, pWallet: DataWallet, pAmountRequired: float = 0.001):
        l_FilePath = os.getcwd() + strLoggingPath.format(
            str(pWallet.mGroup) + "_" + str(pWallet.mAddress))
        try:
            # -------------- Proxy -----------------------------------------

            async with aiohttp.ClientSession() as session:
                l_web3_Base = AsyncWeb3(
                    AsyncWeb3.AsyncHTTPProvider(RPC.BASE_RPC, request_kwargs={'proxy': g_ProxyAddress}))
                await l_web3_Base.provider.cache_async_session(session=session)
                l_bal_base = await l_web3_Base.eth.get_balance(pWallet.mAddress)

                l_web3_OP = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC.OP_RPC, request_kwargs={'proxy': g_ProxyAddress}))
                await l_web3_OP.provider.cache_async_session(session=session)
                l_bal_OP = await l_web3_OP.eth.get_balance(pWallet.mAddress)

                l_web3_arb = AsyncWeb3(
                    AsyncWeb3.AsyncHTTPProvider(RPC.ARB_RPC, request_kwargs={'proxy': g_ProxyAddress}))
                await l_web3_arb.provider.cache_async_session(session=session)
                l_bal_arb = await l_web3_arb.eth.get_balance(pWallet.mAddress)

                l_DictValue = {
                    l_web3_Base: l_bal_base,
                    l_web3_OP: l_bal_OP,
                    l_web3_arb: l_bal_arb,
                }
                l_RPCHasBalance = max(l_DictValue, key=l_DictValue.get)

                if Web3.from_wei(l_DictValue[l_RPCHasBalance], "ether") > pAmountRequired:
                    return l_RPCHasBalance.provider.endpoint_uri
                else:
                    return ""
        except TimeoutError as t:
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.GetChainHaveBalance: TimeoutError\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)
        except Exception as e:
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.GetChainHaveBalance: {type(e).__name__} - {e}\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)

        return None

    async def GetChainHaveETH_and_renzoETH(self, pWallet: DataWallet, pAmountRequired: float = 0.001, pAmountTokenRequired: float = 0.001):
        l_FilePath = os.getcwd() + strLoggingPath.format(
            str(pWallet.mGroup) + "_" + str(pWallet.mAddress))
        l_Balance_renzoETH_Base = None
        l_Balance_renzoETH_op = None
        l_Balance_renzoETH_arb = None

        try:

            async with aiohttp.ClientSession() as session:
                l_web3_Base = AsyncWeb3(
                    AsyncWeb3.AsyncHTTPProvider(RPC.BASE_RPC, request_kwargs={'proxy': g_ProxyAddress}))
                await l_web3_Base.provider.cache_async_session(session=session)
                l_bal_base = await l_web3_Base.eth.get_balance(pWallet.mAddress)
                if l_bal_base > pAmountRequired:
                    l_Token_renzoETH_Base = TokenERC20(l_web3_Base, TokenContract.Base.renzoETH)
                    l_Balance_renzoETH_Base = (await l_Token_renzoETH_Base.BalanceOf(pWallet.mAddress)) / (10 ** gDictTokenDecimal[TokenContract.Base.renzoETH]["Decimal"])

                l_web3_OP = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC.OP_RPC, request_kwargs={'proxy': g_ProxyAddress}))
                await l_web3_OP.provider.cache_async_session(session=session)
                l_bal_OP = await l_web3_OP.eth.get_balance(pWallet.mAddress)
                if l_bal_OP > pAmountRequired:
                    l_Token_renzoETH_op = TokenERC20(l_web3_OP, TokenContract.OP.renzoETH)
                    l_Balance_renzoETH_op = (await l_Token_renzoETH_op.BalanceOf(pWallet.mAddress)) / (10 ** gDictTokenDecimal[TokenContract.OP.renzoETH]["Decimal"])

                l_web3_arb = AsyncWeb3(
                    AsyncWeb3.AsyncHTTPProvider(RPC.ARB_RPC, request_kwargs={'proxy': g_ProxyAddress}))
                await l_web3_arb.provider.cache_async_session(session=session)
                l_bal_arb = await l_web3_arb.eth.get_balance(pWallet.mAddress)
                if l_bal_arb > pAmountRequired:
                    l_Token_renzoETH_arb = TokenERC20(l_web3_arb, TokenContract.ARB.renzoETH)
                    l_Balance_renzoETH_arb = (await l_Token_renzoETH_arb.BalanceOf(pWallet.mAddress)) / (10 ** gDictTokenDecimal[TokenContract.ARB.renzoETH]["Decimal"])

                l_DictValue_Balance_ETH = {
                    l_web3_Base: l_bal_base,
                    l_web3_OP: l_bal_OP,
                    l_web3_arb: l_bal_arb,
                }

                l_DictValue_Balance_Token = {
                    l_web3_Base: l_Balance_renzoETH_Base or 0,
                    l_web3_OP: l_Balance_renzoETH_op or 0,
                    l_web3_arb: l_Balance_renzoETH_arb or 0,
                }
                l_RPCHasBalance_Token = max(l_DictValue_Balance_Token, key=l_DictValue_Balance_Token.get)

                if l_DictValue_Balance_Token[l_RPCHasBalance_Token] > pAmountTokenRequired:
                    if Web3.from_wei(l_DictValue_Balance_ETH[l_RPCHasBalance_Token], "ether") > pAmountRequired:
                        return l_RPCHasBalance_Token.provider.endpoint_uri
                    else:
                        return ""
                else:
                    return ""
        except TimeoutError as t:
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.GetChainHaveETH_and_renzoETH: TimeoutError\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)
        except Exception as e:
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.GetChainHaveETH_and_renzoETH: {type(e).__name__} - {e}\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)

        return None

    async def GetChainHaveBalance_FromListRPC(self, pWallet: DataWallet, pListRPC, pAmountRequired: float = 0.001):
        l_FilePath = os.getcwd() + strLoggingPath.format(
            str(pWallet.mGroup) + "_" + str(pWallet.mAddress))
        l_ListRPC_HaveBalance = []
        try:
            async with aiohttp.ClientSession() as session:
                for l_RPC in pListRPC:
                    l_web3 = AsyncWeb3(
                        AsyncWeb3.AsyncHTTPProvider(l_RPC, request_kwargs={'proxy': g_ProxyAddress}))
                    await l_web3.provider.cache_async_session(session=session)
                    l_bal = await l_web3.eth.get_balance(pWallet.mAddress)

                    if Web3.from_wei(l_bal, "ether") > pAmountRequired:
                        l_ListRPC_HaveBalance.append(l_RPC)

        except TimeoutError as t:
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.GetChainHaveBalance: TimeoutError\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)
        except Exception as e:
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.GetChainHaveBalance: {type(e).__name__} - {e}\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)
        return l_ListRPC_HaveBalance

    async def GetDataWallet(self, pWalletAddress: ChecksumAddress):
        async for session in self.mDatabaseConn.get_session():
            l_WalletsRepo = WalletsRepository(session)
            l_Account = await l_WalletsRepo.get_wallet(pWalletAddress)
            if not l_Account:
                return None
            else:
                return l_Account

    async def Update_IsComplete_Data_Wallet(self, pWalletAddress: ChecksumAddress):
        async for session in self.mDatabaseConn.get_session():
            l_WalletsRepo = WalletsRepository(session)
            await l_WalletsRepo.upsert_wallet_stats(pWalletAddress, pIsComplete=1)


