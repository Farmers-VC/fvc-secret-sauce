import click
import sys

from config import Config
from services.ethereum.ethereum import Ethereum
from services.pools.loader import PoolLoader
from services.strategy.scan import StrategyScan
from services.ttypes.strategy import StrategyEnum


@click.command()
@click.option("--kovan", is_flag=True, help="Point to Kovan test network")
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
    help="Set min Amount to trade with in WETH (Default: 3.0)",
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
    "--gas-multiplier",
    default=1.5,
    help="Set gas price multipler (Default: 1.5)",
)
@click.option(
    "--max-block",
    default=3,
    help="Set max number of block we allow the transaction to go through (Default: 3)",
)
@click.option(
    "--since",
    default="latest",
    help="Since Block (latest|pending) (Default: latest)",
)
@click.option(
    "--only-tokens",
    default="all",
    help="Only filter tokens by name (i.e: --only XIOT,XAMP,UNI) (Default: all)",
)
def scan(
    kovan: bool,
    debug: bool,
    send_tx: bool,
    max_amount: float,
    min_amount: float,
    min_liquidity: int,
    max_liquidity: int,
    gas_multiplier: float,
    max_block: int,
    since: str,
    only_tokens: str,
) -> None:
    print(
        f"-----------------------------------------------------------\n"
        f"------------------ SCANNING SOME ARBS ---------------------\n"
        f"-----------------------------------------------------------\n"
        f"Gas Multiplier: {gas_multiplier}\n"
        f"Max Block Allowed: {max_block}\n"
        f"Sending Transactions on-chain: {send_tx}\n"
        f"Since Block: {since}\n"
        f"Only Tokens: {only_tokens}\n"
        f"-----------------------------------------------------------"
    )
    sys.stdout.flush()
    config = Config(
        strategy=StrategyEnum.SCAN,
        kovan=kovan,
        debug=debug,
        send_tx=send_tx,
        max_amount=max_amount,
        min_amount=min_amount,
        min_liquidity=min_liquidity,
        max_liquidity=max_liquidity,
        gas_multiplier=gas_multiplier,
        max_block=max_block,
        since=since,
        only_tokens=only_tokens,
    )
    pool_loader = PoolLoader(config=config)
    pools = pool_loader.load_all_pools()
    ethereum = Ethereum(config)
    strategy = StrategyScan(
        pools,
        ethereum,
        config=config,
    )
    strategy.scan_arbitrage()


scan()
