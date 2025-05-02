import json
import time
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint

import requests
from web3 import Web3
import ast

from CONSTANT import g_ProxyAddress

from Include.AccountEVM import AccountEVM
from Include.ConnectWeb3 import ConnectWeb3
from Include.Transactions import Transactions

http_proxy = {
                "http": g_ProxyAddress,
                "https": g_ProxyAddress
            }

# session = requests.Session()
# session.proxies.update(http_proxy)
RPC = "https://testnet-rpc.monad.xyz"
web3 = Web3(Web3.HTTPProvider(RPC))
print(web3.is_connected())

abi = '[{"type":"constructor","inputs":[],"stateMutability":"nonpayable"},{"type":"function","name":"claim","inputs":[{"name":"user","type":"address","internalType":"address"},{"name":"token","type":"address","internalType":"address"},{"name":"amount","type":"uint256","internalType":"uint256"}],"outputs":[],"stateMutability":"nonpayable"},{"type":"function","name":"maxClaim","inputs":[],"outputs":[{"name":"","type":"uint256","internalType":"uint256"}],"stateMutability":"view"},{"type":"function","name":"maxSepETHClaim","inputs":[],"outputs":[{"name":"","type":"uint256","internalType":"uint256"}],"stateMutability":"view"},{"type":"function","name":"multiClaim","inputs":[{"name":"user","type":"address","internalType":"address"},{"name":"tokens","type":"address[]","internalType":"address[]"},{"name":"amounts","type":"uint256[]","internalType":"uint256[]"}],"outputs":[],"stateMutability":"nonpayable"},{"type":"function","name":"overrideMaxClaim","inputs":[{"name":"","type":"address","internalType":"address"}],"outputs":[{"name":"","type":"uint256","internalType":"uint256"}],"stateMutability":"view"},{"type":"function","name":"owner","inputs":[],"outputs":[{"name":"","type":"address","internalType":"address"}],"stateMutability":"view"},{"type":"function","name":"renounceOwnership","inputs":[],"outputs":[],"stateMutability":"nonpayable"},{"type":"function","name":"setMaxClaimAmounts","inputs":[{"name":"amountERC20","type":"uint256","internalType":"uint256"},{"name":"amountSepETH","type":"uint256","internalType":"uint256"}],"outputs":[],"stateMutability":"nonpayable"},{"type":"function","name":"setMaxClaimAmounts","inputs":[{"name":"token","type":"address","internalType":"address"},{"name":"amount","type":"uint256","internalType":"uint256"}],"outputs":[],"stateMutability":"nonpayable"},{"type":"function","name":"transferOwnership","inputs":[{"name":"newOwner","type":"address","internalType":"address"}],"outputs":[],"stateMutability":"nonpayable"},{"type":"function","name":"userLastClaimed","inputs":[{"name":"","type":"address","internalType":"address"},{"name":"","type":"address","internalType":"address"}],"outputs":[{"name":"","type":"uint256","internalType":"uint256"}],"stateMutability":"view"},{"type":"event","name":"OwnershipTransferred","inputs":[{"name":"previousOwner","type":"address","indexed":true,"internalType":"address"},{"name":"newOwner","type":"address","indexed":true,"internalType":"address"}],"anonymous":false}]'
abi = json.loads(abi)


token = web3.to_checksum_address("0x2f930b339DE82F34FDbe54e872Eb4A2855B76EA2")

l_FactoryContract = web3.eth.contract(address=token, abi=abi)
pprint(l_FactoryContract.all_functions())



balance = l_FactoryContract.functions.userLastClaimed(web3.to_checksum_address("0x08c91Acd3ad3c2D69152334D009E03154c0cEE2e"),
                                               web3.to_checksum_address("0x6BB379A2056d1304E73012b99338F8F581eE2E18")).call()

print(balance)

