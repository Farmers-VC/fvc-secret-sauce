import os

from web3 import Web3

from services.ethereum.ethereum import Ethereum
from services.exchange.factory import ExchangeFactory
from services.ttypes.contract import ContractTypeEnum

ETHEREUM_WS_URI = os.environ['ETHEREUM_WS_URI']


def main() -> None:
    test_balancer()
    test_uniswap()


def test_balancer() -> None:
    POOL_ADDRESS = '0x59a19d8c652fa0284f44113d0ff9aba70bd46fb4'
    TOKEN_IN_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    TOKEN_OUT_ADDRESS = '0xba100000625a3754423978a60c9317c58a424e3D'
    WETH_AMOUNT_IN = '10000'
    eth_svc = Ethereum(ETHEREUM_WS_URI)
    contract = eth_svc.init_contract(POOL_ADDRESS, ContractTypeEnum.BPOOL)
    exchange = ExchangeFactory.create(contract, ContractTypeEnum.BPOOL)
    # TODO: Ensure that we are currently using the token number of decimal
    amount_out = exchange.calc_amount_out(TOKEN_IN_ADDRESS, TOKEN_OUT_ADDRESS, WETH_AMOUNT_IN)
    print('Balancer Out', Web3.fromWei(amount_out, 'ether'))


def test_uniswap() -> None:
    PAIR_ADDRESS = '0x22dd2b8985a9288341af1265b7a95d00e6d2126e'
    TOKEN_IN_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    TOKEN_OUT_ADDRESS = '0xf5d0fefaab749d8b14c27f0de60cc6e9e7f848d1'
    WETH_AMOUNT_IN = '100'
    eth_svc = Ethereum(ETHEREUM_WS_URI)
    contract = eth_svc.init_contract(PAIR_ADDRESS, ContractTypeEnum.UNISWAP)
    exchange = ExchangeFactory.create(contract, ContractTypeEnum.UNISWAP)
    amount_out = exchange.calc_amount_out(TOKEN_IN_ADDRESS, TOKEN_OUT_ADDRESS, WETH_AMOUNT_IN)
    print('Uniswap out', amount_out)
    # print(Web3.fromWei(amount_out, 'ether'))


main()
