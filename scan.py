import click

from config import Config
from services.algo.scan import AlgoScan
from services.ethereum.ethereum import Ethereum
from services.pools.loader import PoolLoader


@click.command()
@click.option("--kovan", is_flag=True, help="Point to Kovan test network")
@click.option("--debug", is_flag=True, help="Display logs")
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
def scan(
    kovan: bool,
    debug: bool,
    max_amount: float,
    min_amount: float,
) -> None:
    print("-----------------------------------------------------------")
    print("--------------- JUST SCANNING SOME ARBS -------------------")
    print("-----------------------------------------------------------")

    config = Config(
        kovan=kovan,
        debug=debug,
        send_tx=False,
        max_amount=max_amount,
        min_amount=min_amount,
    )
    pool_loader = PoolLoader(config=config)
    pools = pool_loader.load_all_pools()
    ethereum = Ethereum(config)
    algo = AlgoScan(
        pools,
        ethereum,
        config=config,
    )
    algo.scan_arbitrage()


scan()
