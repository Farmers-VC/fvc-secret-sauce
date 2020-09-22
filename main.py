import os
import os.path

import click
from web3 import Web3
from web3.gas_strategies.time_based import construct_time_based_gas_price_strategy

from services.algo.algo import Algo
from services.ethereum.ethereum import Ethereum
from services.pools.loader import PoolLoader

ETHEREUM_WS_URI = os.environ["ETHEREUM_WS_URI"]
KOVAN_ETHEREUM_WS_URI = os.environ["KOVAN_ETHEREUM_WS_URI"]


@click.command()
@click.option("--kovan", is_flag=True, help="Point to Kovan test network")
@click.option("--debug", is_flag=True, help="Display logs")
@click.option("--send-tx", is_flag=True, help="Send arbitrage transactions on-chain")
@click.option(
    "--amount", default=6.0, help="Set max amount to trade with in WETH (Default: 6.0)"
)
def main(kovan: bool, debug: bool, send_tx: bool, amount: float) -> None:
    pool_loader = PoolLoader(kovan=kovan)
    pools = pool_loader.load_all_pools()
    w3 = _init_web3(kovan)
    ethereum = Ethereum(w3, kovan)
    algo = Algo(
        pools,
        ethereum,
        kovan=kovan,
        debug=debug,
        send_tx=send_tx,
        max_amount_in_weth=amount,
    )
    algo.scan_arbitrage()


def _init_web3(kovan) -> Web3:
    w3 = Web3(Web3.WebsocketProvider(ETHEREUM_WS_URI))
    if kovan:
        w3 = Web3(Web3.WebsocketProvider(KOVAN_ETHEREUM_WS_URI))

    gas_strategy = construct_time_based_gas_price_strategy(
        max_wait_seconds=10, sample_size=5, probability=100
    )
    w3.eth.setGasPriceStrategy(gas_strategy)
    return w3


main()
