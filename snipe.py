from typing import List

import click
import yaml
from web3 import Web3

from config import Config
from services.algo.snipe import AlgoSnipe
from services.ethereum.ethereum import Ethereum
from services.pools.loader import PoolLoader
from services.ttypes.sniper import SnipingNoob


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
@click.option("--send-tx", is_flag=True, help="Send the transaction on-chain")
@click.option("--address", help="Specify a specific arbitrageur address to snipe")
def snipe(
    kovan: bool,
    debug: bool,
    max_amount: float,
    min_amount: float,
    send_tx: bool,
    address: str,
) -> None:
    config = Config(
        kovan=kovan,
        debug=debug,
        send_tx=send_tx,
        max_amount=max_amount,
        min_amount=min_amount,
        is_snipe=True,
    )
    print("-----------------------------------------------------------")
    print("----------------- SNIPING SOME NOOOOOBS -------------------")
    print("-----------------------------------------------------------")
    pool_loader = PoolLoader(config=config)
    pools = pool_loader.load_all_pools()
    ethereum = Ethereum(config)
    # breakpoint()
    if address:
        sniping_noobs = [SnipingNoob(address=Web3.toChecksumAddress(address))]
    else:
        sniping_noobs = _load_noobs_yaml(config)
    algo = AlgoSnipe(ethereum, config, pools, sniping_noobs)
    algo.snipe_arbitrageur()


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
