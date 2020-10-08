from typing import List

import click
import yaml
from web3 import Web3

from config import Config
from services.ethereum.ethereum import Ethereum
from services.pools.loader import PoolLoader
from services.strategy.snipe import StrategySnipe
from services.ttypes.sniper import SnipingNoob
from services.ttypes.strategy import StrategyEnum


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
@click.option(
    "--min-liquidity",
    default=20000,
    help="Set minimum liquidity (Default: 30,000)",
)
@click.option(
    "--max-liquidity",
    default=10000000000,
    help="Set max liquidity (Default: 500,000)",
)
@click.option("--send-tx", is_flag=True, help="Send the transaction on-chain")
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
    help="Since Block (latest|pending)(Default: latest)",
)
@click.option(
    "--only-tokens",
    default="",
    help="Only filter tokens by name (i.e: --only XIOT,XAMP,UNI) (Default: '')",
)
@click.option("--address", help="Specify a specific arbitrageur address to snipe")
def snipe(
    kovan: bool,
    debug: bool,
    max_amount: float,
    min_amount: float,
    min_liquidity: int,
    max_liquidity: int,
    send_tx: bool,
    gas_multiplier: float,
    max_block: int,
    since: str,
    only_tokens: str,
    address: str,
) -> None:
    print("-----------------------------------------------------------")
    print("----------------- SNIPING SOME NOOOOOBS -------------------")
    print("-----------------------------------------------------------")
    print(f"Sniping Address: {address}")
    print(f"Gas Multiplier: {gas_multiplier}")
    print(f"Max Block Allowed: {max_block}")
    print(f"Sending Transactions on-chain: {send_tx}")
    print(f"Since Block: {since}")
    print(f"Only Tokens: {only_tokens}")
    print("-----------------------------------------------------------")
    config = Config(
        strategy=StrategyEnum.SNIPE,
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
    if address:
        sniping_noobs = [SnipingNoob(address=Web3.toChecksumAddress(address))]
    else:
        sniping_noobs = _load_noobs_yaml(config)
    strategy = StrategySnipe(ethereum, config, pools, sniping_noobs)
    strategy.snipe_arbitrageur()


def _load_noobs_yaml(config: Config) -> List[SnipingNoob]:
    noobs: List[SnipingNoob] = []
    with open(config.get("SNIPING_NOOBS_YAML_PATH"), "r") as stream:
        noobs_dict = yaml.safe_load(stream)
        if noobs_dict["noobs"]:
            for noob_yaml in noobs_dict["noobs"]:
                noob = SnipingNoob(address=Web3.toChecksumAddress(noob_yaml["address"]))
                noobs.append(noob)
    return noobs


snipe()
