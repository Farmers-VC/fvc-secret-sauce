from typing import List

import yaml
from web3 import Web3

from config import Config
from services.ethereum.ethereum import Ethereum
from services.ttypes.arbitrage import ArbitragePath
from services.ttypes.sniper import SnipingNoob
from services.utils import timer


class Sniper:
    def __init__(self, ethereum: Ethereum, config: Config) -> None:
        self.ethereum = ethereum
        self.config = config
        self._load_noobs_yaml()

    def _load_noobs_yaml(self) -> None:
        noobs: List[SnipingNoob] = []
        with open(self.config.get("SNIPING_NOOBS_YAML_PATH"), "r") as stream:
            noobs_dict = yaml.safe_load(stream)
            if noobs_dict["noobs"]:
                for noob_yaml in noobs_dict["noobs"]:
                    noob = SnipingNoob(
                        address=Web3.toChecksumAddress(noob_yaml["address"])
                    )
                    noobs.append(noob)
            self.noobs = noobs

    @timer
    def scan_mempool_and_snipe(self, arbitrage_path: ArbitragePath):
        """Watch the mempool for an arbitrageur targetting `arbitrage_path`
        Once detected, we snipe them by submitting a transaction with a higher gas price.
        """
        self._scan_mempool(arbitrage_path)

    def _scan_mempool(self, arbitrage_path):
        # pool_and_token_addresses = arbitrage_path.pool_and_token_addresses
        pending_tx = self.ethereum.w3_http.geth.txpool.content()["pending"]
        for noob in self.noobs:
            if noob.address in pending_tx:
                print(pending_tx[noob.address])
        # print(pending_tx)
        # for _, tx_by_nonce in pending_tx.items():
        #     for _, tx in tx_by_nonce.items():
        #         if any(tx["input"] in addr for addr in pool_and_token_addresses):
        #             print("Found arbitrage tx")
        #             print(tx)
