import click

from config import Config
from services.ethereum.ethereum import Ethereum
from services.strategy.fresh import StrategyFresh
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
@click.option(
    "--consecutive",
    default=2,
    help="Set triggering tx after how many consecutive block of arbitrage (Default: 2)",
)
@click.option(
    "--gas-multiplier",
    default=1.5,
    help="Set gas price multipler (Default: 1.5)",
)
@click.option(
    "--max-block",
    default=3,
    help="Set max number of block we allow the transaction to go through (Default: 3)",
)
def fresh(
    kovan: bool,
    debug: bool,
    send_tx: bool,
    max_amount: float,
    min_amount: float,
    min_liquidity: int,
    max_liquidity: int,
    consecutive: int,
    gas_multiplier: float,
    max_block: int,
) -> None:
    print("-----------------------------------------------------------")
    print("--------------- ARBITRAGING FRESH POOLS -------------------")
    print("-----------------------------------------------------------")
    print(f"Consecutive Arbitrage: {consecutive}")
    print(f"Gas Multiplier: {gas_multiplier}")
    print(f"Max Block Allowed: {max_block}")
    print(f"Sending Transactions on-chain: {send_tx}")
    print("-----------------------------------------------------------")
    config = Config(
        strategy=StrategyEnum.FRESH,
        kovan=kovan,
        debug=debug,
        send_tx=send_tx,
        max_amount=max_amount,
        min_amount=min_amount,
        min_liquidity=min_liquidity,
        max_liquidity=max_liquidity,
        gas_multiplier=gas_multiplier,
        max_block=max_block,
    )
    ethereum = Ethereum(config)
    strategy = StrategyFresh(consecutive, ethereum, config)
    strategy.arbitrage_fresh_pools()


fresh()
