import click
import threading
import time

from config import Config
from services.ethereum.ethereum import Ethereum
from services.strategy.fresh import StrategyFresh
from services.pools.loader import PoolLoader
from services.path.path import PathFinder
from services.arbitrage.arbitrage import Arbitrage


@click.command()
@click.option("--kovan", is_flag=True, help="point to kovan test network")
@click.option("--debug", is_flag=True, help="Display logs")
@click.option("--send-tx", is_flag=True, help="Flag to activate sending tx on-chain")
@click.option(
    "--max-amount",
    default=6.0,
    help="Set max amount to trade with in WETH (Default: 6.0)",
)
@click.option(
    "--min-amount",
    default=3.0,
    help="set min amount to trade with in weth (default: 3.0)",
)
@click.option(
    "--min-liquidity",
    default=10000,
    help="Set minimum liquidity (Default: 30,000)",
)
@click.option(
    "--max-liquidity",
    default=8000000,
    help="Set max liquidity (Default: 500,000)",
)
def fresh(
    kovan: bool,
    debug: bool,
    send_tx: bool,
    max_amount: float,
    min_amount: float,
    min_liquidity: int,
    max_liquidity: int,
) -> None:
    print("-----------------------------------------------------------")
    print("--------------- ARBITRAGING FRESH POOLS -------------------")
    print("-----------------------------------------------------------")

    config = Config(
        strategy="fresh",
        kovan=kovan,
        debug=debug,
        send_tx=send_tx,
        max_amount=max_amount,
        min_amount=min_amount,
        min_liquidity=min_liquidity,
        max_liquidity=max_liquidity,
    )
    ethereum = Ethereum(config)
    pool_loader = PoolLoader(config=config)
    while True:
        pools = pool_loader.load_all_pools()
        arbitrage_service = Arbitrage(pools, ethereum, config)
        arbitrage_paths = PathFinder(pools, config).find_all_paths()
        threads = []
        for index, split_arbitrage_paths in enumerate(chunk(arbitrage_paths, 200)):
            print(f"Spinning up thread #{index}")
            thread = threading.Thread(
                target=fresh_thread,
                args=(config, arbitrage_service, ethereum, split_arbitrage_paths),
            )
            threads.append(thread)
            thread.start()
            time.sleep(1)

        print(f"Waiting for {len(threads)} threads to finish.")

        [t.join() for t in threads]


def fresh_thread(config, arbitrage_service, ethereum, arbitrage_paths):
    StrategyFresh(ethereum, arbitrage_service, config).arbitrage_fresh_pools(
        arbitrage_paths
    )


def chunk(pools, num_per_chunk):

    # looping till length l
    for i in range(0, len(pools), num_per_chunk):
        yield pools[i : i + num_per_chunk]


fresh()
