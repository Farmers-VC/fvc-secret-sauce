import click
from web3 import Web3, middleware
from web3.gas_strategies.time_based import construct_time_based_gas_price_strategy

from config import Config
from services.algo.algo import Algo
from services.ethereum.ethereum import Ethereum
from services.pools.loader import PoolLoader


@click.command()
@click.option("--kovan", is_flag=True, help="Point to Kovan test network")
@click.option("--debug", is_flag=True, help="Display logs")
@click.option("--send-tx", is_flag=True, help="Send arbitrage transactions on-chain")
@click.option(
    "--max-amount",
    default=6.0,
    help="Set max amount to trade with in WETH (Default: 6.0)",
)
@click.option(
    "--min-amount",
    default=3.0,
    help="Set min Amount to trade with in WETH (Default: 3.0)",
)
def main(
    kovan: bool, debug: bool, send_tx: bool, max_amount: float, min_amount: float
) -> None:
    config = Config(
        kovan=kovan,
        debug=debug,
        send_tx=send_tx,
        max_amount=max_amount,
        min_amount=min_amount,
    )
    pool_loader = PoolLoader(config=config)
    pools = pool_loader.load_all_pools()
    w3 = _init_web3(config.get("ETHEREUM_WS_URI"))
    ethereum = Ethereum(w3, config)
    algo = Algo(
        pools,
        ethereum,
        config=config,
    )
    algo.scan_arbitrage()


def _init_web3(ethereum_ws_uri: str) -> Web3:
    w3 = Web3(Web3.WebsocketProvider(ethereum_ws_uri))

    gas_strategy = construct_time_based_gas_price_strategy(
        max_wait_seconds=2, sample_size=1, probability=99
    )
    w3.eth.setGasPriceStrategy(gas_strategy)
    # w3.middleware_onion.add(middleware.time_based_cache_middleware)
    # w3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
    # w3.middleware_onion.add(middleware.simple_cache_middleware)
    return w3


main()
