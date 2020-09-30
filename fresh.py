import click
import threading
import time

from config import Config
from services.ethereum.ethereum import Ethereum
from services.strategy.fresh import StrategyFresh


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
    default=30000,
    help="Set minimum liquidity (Default: 30,000)",
)
@click.option(
    "--max-liquidity",
    default=100000,
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

    thread_1 = threading.Thread(
        target=fresh_thread,
        args=(kovan, debug, send_tx, max_amount, min_amount, 10000, 100000),
    )

    thread_2 = threading.Thread(
        target=fresh_thread,
        args=(kovan, debug, send_tx, max_amount, min_amount, 100000, 1000000),
    )

    thread_3 = threading.Thread(
        target=fresh_thread,
        args=(kovan, debug, send_tx, max_amount, min_amount, 50000, 500000),
    )

    thread_4 = threading.Thread(
        target=fresh_thread,
        args=(kovan, debug, send_tx, max_amount, min_amount, 500000, 8000000),
    )

    thread_1.start()
    time.sleep(1)
    thread_2.start()
    time.sleep(1)
    thread_3.start()
    time.sleep(1)
    thread_4.start()


def fresh_thread(
    kovan, debug, send_tx, max_amount, min_amount, min_liquidity, max_liquidity
):

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
    strategy = StrategyFresh(
        ethereum,
        config,
    )
    strategy.arbitrage_fresh_pools()


fresh()
