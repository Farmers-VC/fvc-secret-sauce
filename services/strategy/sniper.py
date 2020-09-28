from typing import Dict, List

from config import Config
from services.ethereum.ethereum import Ethereum
from services.pools.pool import Pool
from services.ttypes.sniper import SnipingNoob
from services.utils import timer


class Sniper:
    def __init__(
        self,
        ethereum: Ethereum,
        config: Config,
        noobs: List[SnipingNoob],
        pools_by_address: Dict[str, Pool],
    ) -> None:
        self.ethereum = ethereum
        self.config = config
        self.noobs = noobs
        self.pools_by_address = pools_by_address

    @timer
    def scan_mempool_and_snipe(self):
        self._scan_mempool()

    def _scan_mempool(self):
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
