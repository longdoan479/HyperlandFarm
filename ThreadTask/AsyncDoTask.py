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
from Repository.TransactionsRepository import TransactionRepository
from Repository.WalletsRepository import WalletsRepository
from Tasks.TaskBridgeETH_UseNexus import TaskBridgeETH_UseNexus
from Tasks.TaskBridgeEnzoETH import TaskBridgeEnzoETH
from Tasks.TaskBridgeHYPER import TaskBridgeHYPER
from Tasks.TaskBridge_OUSDT import TaskBridge_OUSDT
from Tasks.TaskTransferToken_MultiToOne import TaskTransferToken_MultiToOne


class AsyncDoTask:
    def __init__(self, pThreadName, pListAccount: List[DataWallet], pDatabaseConn: AsyncPostgresClient):
        self.mThreadName = pThreadName
        self.mListAccount = pListAccount
        self.mDictAccTxnNumber = {}
        self.mDatabaseConn = pDatabaseConn

    async def run(self):
        random.shuffle(self.mListAccount)
        # await self.HyperlandFarm_BridgeETH()
        # await self.HyperlandFarm_Bridge_renzoETH()
        # await self.HyperlandFarm_Bridge_HYPER_FromBSC()
        await self.HyperlandFarm_Bridge_OUSDT()
        # await self.SendToken_From_Multi_To_One()

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

    async def HyperlandFarm_Bridge_HYPER_FromBSC(self):
        try:
            l_IsAllAccReachTarget = False
            while not l_IsAllAccReachTarget:
                for i in range(0, len(self.mListAccount)):
                    self.mListAccount[i].mAddress = Web3.to_checksum_address(self.mListAccount[i].mAddress)
                    l_FilePath = os.getcwd() + strLoggingPath.format(
                        str(self.mListAccount[i].mGroup) + "_" + str(self.mListAccount[i].mAddress))
                    try:
                        l_RPC_From = await self.CheckBSC_HasBalnce_BNB_And_HYPER(self.mListAccount[i], 0.001, 1)

                        # if l_RPC_From == "" or l_RPC_From is None:
                        #     continue
                        print(f"{self.mThreadName}: Wallet {self.mListAccount[i].mAddress}, RPC {l_RPC_From}")

                        l_DataWallet = await self.GetDataWallet(self.mListAccount[i].mAddress)

                        l_wallet_entry = self.mDictAccTxnNumber.get(self.mListAccount[i].mAddress)

                        # Check if wallet exists in dictionary
                        if l_wallet_entry is None:
                            # Initialize new wallet entry
                            l_RandomTarget = random.randint(9, 10)

                            # Determine if wallet is complete based on database status or lack of balance
                            if l_DataWallet is not None and l_DataWallet.is_complete == 1:
                                # Wallet is marked complete in database
                                l_is_complete = True
                            elif l_RPC_From == "":
                                # No balance available, mark as complete to skip it
                                l_is_complete = True
                                await self.Update_IsComplete_Data_Wallet(self.mListAccount[i].mAddress)

                            else:
                                # Has balance and not marked complete - needs processing
                                l_is_complete = False

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
                            if (l_DataWallet is not None and l_DataWallet.is_complete == 1) or l_RPC_From == "":
                                l_wallet_entry["IsDone"] = True
                                await self.Update_IsComplete_Data_Wallet(self.mListAccount[i].mAddress)
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

                            l_TaskBridgeToken_UseNexus = TaskBridgeHYPER(l_Web3, l_Account, self.mDatabaseConn)
                            l_ResultTask = await l_TaskBridgeToken_UseNexus.DoTask(l_ChainID_From, l_ChainID_To, random.randint(1, 3))

                            # if l_ResultTask == EnumStatusTask.SUCCESS:
                            #     l_DataWallet = await self.GetDataWallet(self.mListAccount[i].mAddress)
                            #
                            #     if l_DataWallet is not None and self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["TargetTxnAmount"] <= l_DataWallet.total_txn:
                            #         await self.Update_IsComplete_Data_Wallet(self.mListAccount[i].mAddress)
                        await asyncio.sleep(random.randint(100, 300))


                    except Exception as e:
                        l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.HyperlandFarm_Bridge_renzoETH: {type(e).__name__} - {e}\n\n'
                        Logging.WriteLog(l_FilePath, l_TextToLog)
                        print(f"{self.mThreadName}: =>")
                        traceback.print_exc()

                l_IsAllAccReachTarget = all(wallet["IsDone"] == True for wallet in self.mDictAccTxnNumber.values())
                l_RandomSleep = random.randint(500, 3000)
                print(f"{self.mThreadName}: => Sleeping for {l_RandomSleep}s before next round")
                await asyncio.sleep(l_RandomSleep)
                random.shuffle(self.mListAccount)

        except Exception as e:
            l_FilePath = os.getcwd() + "/unknown_error.txt"
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.HyperlandFarm_Bridge_HYPER_FromBSC: {type(e).__name__} - {e}\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)
            print(f"{self.mThreadName}: =>")
            traceback.print_exc()

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

    async def CheckBSC_HasBalnce_BNB_And_HYPER(self, pWallet: DataWallet, pAmountRequired: float = 0.001, pAmountTokenRequired: float = 0.001):
        l_FilePath = os.getcwd() + strLoggingPath.format(
            str(pWallet.mGroup) + "_" + str(pWallet.mAddress))
        l_Balance_HYPER_BSC = None

        try:

            async with aiohttp.ClientSession() as session:
                l_web3_BSC = AsyncWeb3(
                    AsyncWeb3.AsyncHTTPProvider(RPC.BSC_RPC, request_kwargs={'proxy': g_ProxyAddress}))
                await l_web3_BSC.provider.cache_async_session(session=session)
                l_bal_BSC = await l_web3_BSC.eth.get_balance(pWallet.mAddress)
                if Web3.from_wei(l_bal_BSC, "ether") > pAmountRequired:
                    l_Token_HYPER_BSC = TokenERC20(l_web3_BSC, TokenContract.BSC.HYPER)
                    l_Balance_HYPER_BSC = (await l_Token_HYPER_BSC.BalanceOf(pWallet.mAddress)) / (
                                10 ** gDictTokenDecimal[TokenContract.BSC.HYPER]["Decimal"])


                l_DictValue_Balance_ETH = {
                    l_web3_BSC: l_bal_BSC,
                }

                l_DictValue_Balance_Token = {
                    l_web3_BSC: l_Balance_HYPER_BSC or 0,
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
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.CheckBSC_HasBalnce_BNB_And_HYPER: TimeoutError\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)
        except Exception as e:
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.CheckBSC_HasBalnce_BNB_And_HYPER: {type(e).__name__} - {e}\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)

        return None

    async def SendToken_From_Multi_To_One(self):
        l_IsAllAccReachTarget = False
        while not l_IsAllAccReachTarget:
            for i in range(0, len(self.mListAccount)):
                self.mListAccount[i].mAddress = Web3.to_checksum_address(self.mListAccount[i].mAddress)
                l_FilePath = os.getcwd() + strLoggingPath.format(
                    str(self.mListAccount[i].mGroup) + "_" + str(self.mListAccount[i].mAddress))
                try:
                    if self.mListAccount[i].mAddress not in self.mDictAccTxnNumber:
                        self.mDictAccTxnNumber[self.mListAccount[i].mAddress] = {}
                        self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["IsDone"] = False

                    if self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["IsDone"]:
                        continue

                    print(f"{i}.{str(self.mListAccount[i].mAddress)}: {self.mThreadName}")

                    async with aiohttp.ClientSession() as session:
                        l_Web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC.BASE_RPC, request_kwargs={'proxy': g_ProxyAddress}))
                        await l_Web3.provider.cache_async_session(session=session)
                        l_Account = AccountEVM(self.mListAccount[i].mPrivateKey, l_Web3, self.mListAccount[i].mGroup)

                        l_TaskTransfer = TaskTransferToken_MultiToOne(l_Web3, l_Account)
                        l_ResultTask = await l_TaskTransfer.DoTask()

                        self.mDictAccTxnNumber[self.mListAccount[i].mAddress]["IsDone"] = True if l_ResultTask == EnumStatusTask.SUCCESS else False

                except Exception as e:
                    l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.SendToken_From_Multi_To_One: {type(e).__name__} - {e}\n\n'
                    Logging.WriteLog(l_FilePath, l_TextToLog)
                    print(f"{self.mThreadName}: =>")
                    traceback.print_exc()

            l_IsAllAccReachTarget = all(wallet["IsDone"] == True for wallet in self.mDictAccTxnNumber.values())

    async def HyperlandFarm_Bridge_OUSDT(self):
        l_IsAllAccReachTarget = False
        l_OpenDay = None
        l_IsBreak = False
        while not l_IsAllAccReachTarget:
            if l_IsBreak:
                break

            random.shuffle(self.mListAccount)
            for i in range(0, len(self.mListAccount)):
                if l_IsBreak:
                    break
                l_Now = datetime.now()
                if l_OpenDay is None or l_Now.date() >= l_OpenDay.date():
                    l_OpenDay = datetime(l_Now.year, l_Now.month, l_Now.day, 0, 0, 0)
                    l_RandomTarget = random.randint(1, 2)

                self.mListAccount[i].mAddress = Web3.to_checksum_address(self.mListAccount[i].mAddress)
                l_FilePath = os.getcwd() + strLoggingPath.format(
                    str(self.mListAccount[i].mGroup) + "_" + str(self.mListAccount[i].mAddress))
                try:
                    l_Txn_data = await self.QueryTransactionData_by_datatime(self.mListAccount[i].mAddress, l_OpenDay, l_Now)
                    if l_Txn_data is not None and len(l_Txn_data) >= l_RandomTarget:
                        continue


                    l_RPC_From = await self.GetChainHaveETH_and_OUSDT(self.mListAccount[i])

                    if l_RPC_From == "" or l_RPC_From is None:
                        continue
                    print(f"{self.mThreadName}: Wallet {self.mListAccount[i].mAddress}, RPC {l_RPC_From}")

                    l_DataWallet = await self.GetDataWallet(self.mListAccount[i].mAddress)

                    l_wallet_entry = self.mDictAccTxnNumber.get(self.mListAccount[i].mAddress)

                    # Check if wallet exists in dictionary
                    if l_wallet_entry is None:
                        # Initialize new wallet entry
                        l_is_complete = False if l_DataWallet is None or l_DataWallet.is_complete == 0 else True
                        self.mDictAccTxnNumber[self.mListAccount[i].mAddress] = {
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
                        RPC.BASE_RPC,
                    ]
                    l_RoutePath = [l_rpc for l_rpc in l_RoutePath if l_rpc != l_RPC_From]
                    l_RPC_HaveBalance = await self.GetChainHaveBalance_FromListRPC(self.mListAccount[i], l_RoutePath,
                                                                                   0.001)

                    if len(l_RPC_HaveBalance) > 0:
                        l_RPC_To = random.choice(l_RPC_HaveBalance)

                        l_ChainID_From = gDictChainID[l_RPC_From]["chainID"]
                        l_ChainID_To = gDictChainID[l_RPC_To]["chainID"]
                        async with aiohttp.ClientSession() as session:
                            l_Web3 = AsyncWeb3(
                                AsyncWeb3.AsyncHTTPProvider(l_RPC_From, request_kwargs={'proxy': g_ProxyAddress}))
                            await l_Web3.provider.cache_async_session(session=session)
                            l_Account = AccountEVM(self.mListAccount[i].mPrivateKey, l_Web3,
                                                   self.mListAccount[i].mGroup)


                            await asyncio.sleep(random.randint(20, 120))



                            l_TaskBridgeToken_UseNexus = TaskBridge_OUSDT(l_Web3, l_Account, self.mDatabaseConn)
                            l_ResultTask = await l_TaskBridgeToken_UseNexus.DoTask(l_ChainID_From, l_ChainID_To, float(round(random.uniform(20, 60), 3)))

                            if l_ResultTask == EnumStatusTask.SUCCESS:
                                pass
                                # NOTE: Run until out of balance so i can not get the number of transaction
                                # l_DataWallet = await self.GetDataWallet(self.mListAccount[i].mAddress)
                                #
                                # if l_DataWallet is not None and self.mDictAccTxnNumber[self.mListAccount[i].mAddress][
                                #     "TargetTxnAmount"] <= l_DataWallet.total_txn:
                                #     await self.Update_IsComplete_Data_Wallet(self.mListAccount[i].mAddress)

                        l_IsAllAccReachTarget = all(
                            wallet["IsDone"] == True for wallet in self.mDictAccTxnNumber.values())
                        await asyncio.sleep(random.randint(300, 500))

                except Exception as e:
                    l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.HyperlandFarm_Bridge_renzoETH: {type(e).__name__} - {e}\n\n'
                    Logging.WriteLog(l_FilePath, l_TextToLog)
                    print(f"{self.mThreadName}: =>")
                    traceback.print_exc()

            l_RandomSleep = random.randint(500, 3000)
            print(f"{self.mThreadName}: => Sleeping for {l_RandomSleep}s before next round")
            await asyncio.sleep(l_RandomSleep)
            random.shuffle(self.mListAccount)

    async def QueryTransactionData_by_datatime(self, pWalletAddress: ChecksumAddress, pStartDate: datetime, pEndDate: datetime):
        async for session in self.mDatabaseConn.get_session():
            l_TransactionRepo = TransactionRepository(session)
            l_Txn = await l_TransactionRepo.get_transaction_by_datetime(pStartDate, pEndDate, pWalletAddress)
            if not l_Txn:
                return None
            else:
                return l_Txn

    async def GetChainHaveETH_and_OUSDT(self, pWallet: DataWallet, pAmountRequired: float = 0.00009, pAmountTokenRequired: float = 0.2):
        l_FilePath = os.getcwd() + strLoggingPath.format(
            str(pWallet.mGroup) + "_" + str(pWallet.mAddress))
        l_Balance_OUSDT_Base = None
        l_Balance_OUSDT_op = None

        try:
            async with aiohttp.ClientSession() as session:
                l_web3_Base = AsyncWeb3(
                    AsyncWeb3.AsyncHTTPProvider(RPC.BASE_RPC, request_kwargs={'proxy': g_ProxyAddress}))
                await l_web3_Base.provider.cache_async_session(session=session)
                l_bal_base = await l_web3_Base.eth.get_balance(pWallet.mAddress)
                if l_bal_base > pAmountRequired:
                    l_Token_Base = TokenERC20(l_web3_Base, TokenContract.Base.OUSDT)
                    l_Balance_OUSDT_Base = await l_Token_Base.BalanceOf(pWallet.mAddress, True)

                l_web3_OP = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC.OP_RPC, request_kwargs={'proxy': g_ProxyAddress}))
                await l_web3_OP.provider.cache_async_session(session=session)
                l_bal_OP = await l_web3_OP.eth.get_balance(pWallet.mAddress)
                if l_bal_OP > pAmountRequired:
                    l_Token_op = TokenERC20(l_web3_OP, TokenContract.OP.OUSDT)
                    l_Balance_OUSDT_op = await l_Token_op.BalanceOf(pWallet.mAddress, True)

                l_DictValue_Balance_ETH = {
                    l_web3_Base: l_bal_base,
                    l_web3_OP: l_bal_OP,
                }

                l_DictValue_Balance_Token = {
                    l_web3_Base: l_Balance_OUSDT_Base or 0,
                    l_web3_OP: l_Balance_OUSDT_op or 0,
                }

                # Get chains that meet both conditions
                l_ValidChains = []
                for web3_instance, token_balance in l_DictValue_Balance_Token.items():
                    eth_balance = l_DictValue_Balance_ETH[web3_instance]
                    if (token_balance > pAmountTokenRequired and
                            Web3.from_wei(eth_balance, "ether") > pAmountRequired):
                        l_ValidChains.append(web3_instance.provider.endpoint_uri)

                # Return random choice from valid chains or empty string
                if len(l_ValidChains) > 0:
                    return random.choice(l_ValidChains)
                else:
                    return ""

        except TimeoutError as t:
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.GetChainHaveETH_and_OUSDT: TimeoutError\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)
        except Exception as e:
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: ThreadDoTask.GetChainHaveETH_and_OUSDT: {type(e).__name__} - {e}\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)

        return None
