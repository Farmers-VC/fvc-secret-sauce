import click
import threading
import time

from config import Config
from services.ethereum.ethereum import Ethereum
from services.strategy.fresh import StrategyFresh

LIQUIDITY_RANGES = [
    (10000, 100000),
    (100000, 1000000),
    (50000, 500000),
    (500000, 8000000),
]


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
def fresh(
    kovan: bool,
    debug: bool,
    send_tx: bool,
    max_amount: float,
    min_amount: float,
) -> None:
    print("-----------------------------------------------------------")
    print("--------------- ARBITRAGING FRESH POOLS -------------------")
    print("-----------------------------------------------------------")

    for min_liquidity, max_liquidity in LIQUIDITY_RANGES:
        threading.Thread(
            target=fresh_thread,
            args=(
                kovan,
                debug,
                send_tx,
                max_amount,
                min_amount,
                min_liquidity,
                max_liquidity,
            ),
        ).start()
        time.sleep(0.1)


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
