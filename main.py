import os
import os.path

from web3 import Web3

from services.algo.algo import Algo
# from services.ethereum.ethereum import Ethereum
# from services.exchange.factory import ExchangeFactory
from services.pools.loader import PoolLoader

# from services.ttypes.contract import ContractTypeEnum

ETHEREUM_WS_URI = os.environ["ETHEREUM_WS_URI"]
THIS_DIR = os.path.abspath(os.path.dirname(__file__))


def main() -> None:
    pools = load_all_pools()
    # breakpoint()
    w3 = _init_web3()
    # breakpoint()
    algo = Algo(pools, w3)
    algo.scan_arbitrage()


def _init_web3() -> Web3:
    return Web3(Web3.WebsocketProvider(ETHEREUM_WS_URI))


def load_all_pools():
    uniswap_pools = PoolLoader.load_uniswap_pools()
    # token_yaml_path = os.path.join(THIS_DIR, f"pools/tokens.yaml")
    # pools_yaml_path = os.path.join(THIS_DIR, f"pools/pools.yaml")
    # yaml_pools = PoolLoader.load_pools_yaml(token_yaml_path, pools_yaml_path)
    return uniswap_pools
    # return yaml_pools


main()
