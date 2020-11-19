import click
import sys

from config import Config
from services.ethereum.ethereum import Ethereum
from services.strategy.watcher import StrategyWatcher
from services.ttypes.strategy import StrategyEnum


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
    default=1.0,
    help="set min amount to trade with in weth (default: 1.0)",
)
@click.option(
    "--consecutive",
    default=2,
    help="Set triggering tx after how many consecutive block of arbitrage (Default: 2)",
)
@click.option(
    "--gas-multiplier",
    default=1.1,
    help="Set gas price multipler (Default: 1.1)",
)
@click.option(
    "--max-block",
    default=3,
    help="Set max number of block we allow the transaction to go through (Default: 3)",
)
def watcher(
    kovan: bool,
    debug: bool,
    send_tx: bool,
    max_amount: float,
    min_amount: float,
    consecutive: int,
    gas_multiplier: float,
    max_block: int,
) -> None:
    print(
        f"-----------------------------------------------------------\n"
        f"--------------- ARBITRAGING FRESH POOLS -------------------\n"
        f"-----------------------------------------------------------\n"
        f"Consecutive Arbitrage: {consecutive}\n"
        f"Gas Multiplier: {gas_multiplier}\n"
        f"Max Block Allowed: {max_block}\n"
        f"Sending Transactions on-chain: {send_tx}\n"
        f"-----------------------------------------------------------"
    )
    sys.stdout.flush()
    config = Config(
        strategy=StrategyEnum.FRESH,
        kovan=kovan,
        debug=debug,
        send_tx=send_tx,
        max_amount=max_amount,
        min_amount=min_amount,
        min_liquidity=None,
        max_liquidity=None,
        gas_multiplier=gas_multiplier,
        max_block=max_block,
    )
    ethereum = Ethereum(config)
    strategy = StrategyWatcher(consecutive, ethereum, config)
    strategy.watch()


watcher()
