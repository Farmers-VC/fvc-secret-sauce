import os
import os.path

import click
from web3 import Web3
from web3.gas_strategies.time_based import construct_time_based_gas_price_strategy

from services.algo.algo import Algo
from services.ethereum.ethereum import Ethereum
from services.pools.loader import PoolLoader

ETHEREUM_WS_URI = os.environ["ETHEREUM_WS_URI"]
THIS_DIR = os.path.abspath(os.path.dirname(__file__))
ETHEREUM_WS_URI_KOVAN = os.environ["ETHEREUM_WS_URI_KOVAN"]


@click.command()
@click.option("--kovan", is_flag=True)
@click.option("--debug", is_flag=True)
def main(kovan: bool, debug: bool) -> None:
    pools = load_all_pools(kovan)
    w3 = _init_web3(kovan)
    ethereum = Ethereum(w3, kovan)
    algo = Algo(pools, ethereum, kovan=kovan, debug=debug)
    algo.scan_arbitrage()


def _init_web3(kovan) -> Web3:
    w3 = Web3(Web3.WebsocketProvider(ETHEREUM_WS_URI))
    if kovan:
        w3 = Web3(Web3.WebsocketProvider(ETHEREUM_WS_URI_KOVAN))

    gas_strategy = construct_time_based_gas_price_strategy(
        max_wait_seconds=10, sample_size=5, probability=100
    )
    w3.eth.setGasPriceStrategy(gas_strategy)
    return w3


def load_all_pools(kovan):
    if kovan:
        return _load_kovan_pools()

    uniswap_pools = PoolLoader.load_uniswap_pools()
    balancer_pools = PoolLoader.load_balancer_pools()
    token_yaml_path = os.path.join(THIS_DIR, f"pools/tokens.yaml")
    pools_yaml_path = os.path.join(THIS_DIR, f"pools/pools.yaml")
    yaml_pools = PoolLoader.load_pools_yaml(token_yaml_path, pools_yaml_path)
    return uniswap_pools + balancer_pools + yaml_pools


def _load_kovan_pools():
    token_yaml_path = os.path.join(THIS_DIR, f"pools/kovan/tokens.yaml")
    pools_yaml_path = os.path.join(THIS_DIR, f"pools/kovan/pools.yaml")
    yaml_pools = PoolLoader.load_pools_yaml(token_yaml_path, pools_yaml_path)
    return yaml_pools


main()
