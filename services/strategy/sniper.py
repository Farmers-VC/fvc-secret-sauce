import re
from typing import Dict, List

from config import Config
from services.ethereum.ethereum import Ethereum
from services.pools.pool import Pool
from services.ttypes.sniper import SnipingArbitrage, SnipingNoob
from services.utils import timer

ARGUMENT_LENGTH = 64


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
    def scan_mempool_and_snipe(self) -> List[SnipingArbitrage]:
        """
        Watch the mempool for an arbitrageur targetting `arbitrage_path`
        Once detected, we snipe them by submitting a transaction with a higher gas price.
        """
        all_pending_txs = self.ethereum.w3_http.geth.txpool.content()["pending"]

        arbitrage: List[SnipingArbitrage] = []
        for noob in self.noobs:
            if noob.address in all_pending_txs:
                for pending_tx in all_pending_txs[noob.address].values():
                    arbitrage.append(
                        SnipingArbitrage(
                            pools=self._get_pools(pending_tx["input"]),
                            gas_price=int(pending_tx["gasPrice"], 16),
                            tx_hash=pending_tx["hash"],
                        )
                    )
        if self.config.debug:
            print(f"Mempool: {arbitrage}")

        return arbitrage

    def _get_pools(self, contract_input: str) -> List[Pool]:
        """
        Split contract input into arguments and check each argument to see if it is a pool arg.
        Returns a list of Pool objects
        """
        pools: List[Pool] = []
        for arg in re.findall(".{%d}" % ARGUMENT_LENGTH, contract_input[2:]):
            address = f"0x{arg[2:42]}"
            if address in self.pools_by_address:
                pools.append(self.pools_by_address[address])

        return pools
