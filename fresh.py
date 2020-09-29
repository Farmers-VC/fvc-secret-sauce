import click

from config import Config
from services.algo.fresh import AlgoFresh
from services.ethereum.ethereum import Ethereum


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
    default=500000,
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
    algo = AlgoFresh(
        ethereum,
        config,
    )
    algo.arbitrage_fresh_pools()


fresh()
