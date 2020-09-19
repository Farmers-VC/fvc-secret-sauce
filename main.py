import os
import os.path

from web3 import Web3

from services.algo.algo import Algo
from services.ethereum.ethereum import Ethereum
from services.exchange.factory import ExchangeFactory
from services.pools.loader import PoolLoader
from services.ttypes.contract import ContractTypeEnum

ETHEREUM_WS_URI = os.environ["ETHEREUM_WS_URI"]
THIS_DIR = os.path.abspath(os.path.dirname(__file__))


def main() -> None:
    pools = load_all_pools()
    w3 = _init_web3()
    algo = Algo(pools, w3)
    algo.find_arbitrage()
    # test_balancer(pools[1])
    # test_uniswap(pools[-1])


def _init_web3() -> Web3:
    return Web3(Web3.WebsocketProvider(ETHEREUM_WS_URI))


def test_balancer(pool) -> None:
    # POOL_ADDRESS = '0x59a19d8c652fa0284f44113d0ff9aba70bd46fb4'
    # TOKEN_IN_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    # TOKEN_OUT_ADDRESS = '0xba100000625a3754423978a60c9317c58a424e3D'
    WETH_AMOUNT_IN = Web3.toWei("100", "ether")
    eth_svc = Ethereum(ETHEREUM_WS_URI)
    contract = eth_svc.init_contract(pool.address, ContractTypeEnum.BPOOL)
    exchange = ExchangeFactory.create(contract, ContractTypeEnum.BPOOL)
    amount_out_wei = exchange.calc_amount_out(
        pool.tokens[0], pool.tokens[1], WETH_AMOUNT_IN
    )
    print("Balancer Out", pool.tokens[1].from_wei(amount_out_wei))


def test_uniswap(pool) -> None:
    # PAIR_ADDRESS = '0x22dd2b8985a9288341af1265b7a95d00e6d2126e'
    # TOKEN_IN_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    # TOKEN_OUT_ADDRESS = '0xf5d0fefaab749d8b14c27f0de60cc6e9e7f848d1'
    WETH_AMOUNT_IN = Web3.toWei("100", "ether")
    eth_svc = Ethereum(ETHEREUM_WS_URI)
    contract = eth_svc.init_contract(pool.address, ContractTypeEnum.UNISWAP)
    exchange = ExchangeFactory.create(contract, ContractTypeEnum.UNISWAP)
    amount_out_wei = exchange.calc_amount_out(
        pool.tokens[0], pool.tokens[1], WETH_AMOUNT_IN
    )
    print("Uniswap Out", pool.tokens[1].from_wei(amount_out_wei))


def load_all_pools():
    return PoolLoader.load_uniswap_pools()
    # token_yaml_path = os.path.join(THIS_DIR, f'pools/tokens.yaml')
    # pools_yaml_path = os.path.join(THIS_DIR, f'pools/pools.yaml')
    # pools = PoolLoader.load_pools_yaml(token_yaml_path, pools_yaml_path)
    # return pools


main()
