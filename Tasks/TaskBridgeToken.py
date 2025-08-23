import decimal
import os
import random
from datetime import datetime

from web3 import AsyncWeb3

from CONSTANT import strLoggingPath, EnumStatusTask, gDictTokenDecimal
from IncludeAsync.AccountEVM import AccountEVM
from IncludeAsync.BaseTask import BaseTask
from IncludeAsync.Bridge.UseNexus import UseNexus
from IncludeAsync.Database.AsyncPostgresClient import AsyncPostgresClient
from IncludeAsync.TokenERC20.TokenERC20 import TokenERC20
from Logging import Logging
from Repository.TransactionsRepository import TransactionRepository
from Repository.WalletsRepository import WalletsRepository


class TaskBridgeToken(BaseTask):
    def __init__(self, pWeb3: AsyncWeb3, pAccountEVM: AccountEVM, pDatabaseConn: AsyncPostgresClient):
        super().__init__(pWeb3, pAccountEVM, pDatabaseConn)


    async def DoTask(self, pChainID_From: int, pChainID_To: int, pPercentageAmount: float = 100):
        l_FilePath = os.getcwd() + strLoggingPath.format(
            str(self.mAccountEVM.mGroup) + "_" + str(self.mAccountEVM.GetAddress()))
        l_resultTask = EnumStatusTask.FAILED

        try:
            l_GasPrice = await self.mWeb3.eth.gas_price
            l_TokenAddress = await self.Get_Token_Address(pChainID_From)

            if l_TokenAddress is not None:
                l_UseNexus = UseNexus(self.mWeb3, self.mAccountEVM)
                l_Token = TokenERC20(self.mWeb3, l_TokenAddress)
                l_BalanceToken = await l_Token.BalanceOf(self.mAccountEVM.GetAddress())

                if l_BalanceToken > 0:
                    l_AmountToBridge = round((l_BalanceToken / (10 ** gDictTokenDecimal[l_TokenAddress]["Decimal"])) * pPercentageAmount / 100, random.randint(3, 6))
                    l_ContractToApprove = await l_UseNexus.GetBridgeTokenAddress(l_TokenAddress)
                    l_IsApprove = await self.ApproveToken(l_Token, l_ContractToApprove, l_AmountToBridge*2)

                    if l_IsApprove:
                        l_BalanceETH_Before = await self.mAccountEVM.GetBalanceETH(pIsConvertToEther=True)

                        l_TxnBridge, l_IsSuccessTXN, l_QuoteGasPayment, l_TxnFee = await l_UseNexus.BridgeToken(
                            l_TokenAddress,
                            l_AmountToBridge,
                            pChainID_To,
                            self.mAccountEVM.GetAddress(),
                            l_GasPrice,
                        )

                        if l_IsSuccessTXN:
                            l_BalanceETH_After = await self.mAccountEVM.GetBalanceETH(pIsConvertToEther=True)
                            l_RealQuoteGas = l_BalanceETH_Before - l_BalanceETH_After - self.mWeb3.from_wei(l_TxnFee, "ether")
                            async for session in self.mDatabaseConn.get_session():
                                l_WalletsRepo = WalletsRepository(session)
                                await l_WalletsRepo.upsert_wallet_stats(self.mAccountEVM.GetAddress(),
                                                                        self.mWeb3.from_wei(l_TxnFee, "ether")+l_RealQuoteGas,
                                                                        decimal.Decimal(l_AmountToBridge),
                                                                        l_RealQuoteGas)

                                l_TransactionRepo = TransactionRepository(session)
                                await l_TransactionRepo.upsert_transaction_stats(l_TxnBridge,
                                                                                 self.mAccountEVM.GetAddress(),
                                                                                 self.mWeb3.from_wei(l_TxnFee, "ether"),
                                                                                 decimal.Decimal(l_AmountToBridge),
                                                                                 l_RealQuoteGas,
                                                                                 await self.GetChainID())

                            l_TextToLog = f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: {self.__class__.__name__} - Account {self.mAccountEVM.GetAddress()}:' \
                                          f'\n => Bridge from {pChainID_From} to {pChainID_To}\n' \
                                          f'\n => {str(l_TxnBridge)}\n' \
                                            f'\n => ETH before: {l_BalanceETH_Before}, ETH after: {l_BalanceETH_After}, QuoteGasPayment: {l_QuoteGasPayment}, RealGasPayment: {l_RealQuoteGas}, TxnFee: {self.mWeb3.from_wei(l_TxnFee, "ether")}\n'
                            Logging.WriteLog(l_FilePath, l_TextToLog)
                            l_resultTask = EnumStatusTask.SUCCESS
                        else:
                            l_TextToLog = f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: {self.__class__.__name__} - Account {self.mAccountEVM.GetAddress()}:' \
                                          f'\n => Bridge from {pChainID_From} to {pChainID_To}\n' \
                                          f'\n => Failed \n'
                            Logging.WriteLog(l_FilePath, l_TextToLog)
                else:
                    l_TextToLog = f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: {self.__class__.__name__} - Account {self.mAccountEVM.GetAddress()}:' \
                                  f'\n => No token balance\n'
                    Logging.WriteLog(l_FilePath, l_TextToLog)
        except Exception as e:
            l_TextToLog = f'\n\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: {self.__class__.__name__}: {type(e).__name__} - {e}\n\n'
            Logging.WriteLog(l_FilePath, l_TextToLog)

        return l_resultTask

    async def Get_Token_Address(self, pChainID_From: int):
        raise NotImplementedError("Get_Token_Address method is not implemented.")
