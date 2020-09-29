import re
from typing import List, Set

from config import Config
from services.arbitrage.arbitrage import Arbitrage
from services.ethereum.ethereum import Ethereum
from services.notifications.notifications import Notification
from services.path.path import PathFinder
from services.pools.pool import Pool
from services.printer.printer import PrinterContract
from services.ttypes.arbitrage import ArbitragePath
from services.ttypes.sniper import SnipingArbitrage, SnipingNoob

ARGUMENT_LENGTH = 64


class StrategySnipe:
    def __init__(
        self, ethereum: Ethereum, config: Config, pools: List[Pool], noobs: SnipingNoob
    ) -> None:
        self.ethereum = ethereum
        self.config = config
        self.pools_by_address = {pool.address: pool for pool in pools}
        self.noobs = noobs
        self.arbitrage = Arbitrage(pools, self.ethereum, self.config)
        self.notification = Notification(self.config)
        self.printer = PrinterContract(self.ethereum, self.notification, self.config)
        self.last_txs: List[str] = []

    def snipe_arbitrageur(self) -> None:
        while True:
            latest_block = self.ethereum.w3.eth.blockNumber
            # start_time = time.time()
            sniping_arbitrages: List[SnipingArbitrage] = self._scan_mempool_and_snipe()
            for sniping_arbitrage in sniping_arbitrages:
                path_finder = PathFinder(sniping_arbitrage.pools, self.config)
                arbitrage_paths: List[ArbitragePath] = path_finder.find_all_paths()
                if arbitrage_paths:
                    print(
                        f"[Tx: {sniping_arbitrage.tx_hash}] Found {len(arbitrage_paths)} paths"
                    )
                positive_arbitrages = self.arbitrage.calc_arbitrage(
                    arbitrage_paths,
                    latest_block,
                    sniping_arbitrage.gas_price + 1,
                    sniping_arbitrage.tx_hash,
                )

                for positive_arb in positive_arbitrages:
                    print(positive_arb.print(latest_block, sniping_arbitrage.tx_hash))
                    self.printer.arbitrage_on_chain(
                        positive_arb,
                        latest_block,
                        tx_hash=sniping_arbitrage.tx_hash,
                        send_tx=self.config.send_tx,
                    )
            # gas_price = sniping_arbitrages[-1].gas_price if sniping_arbitrages else 0
            # print(
            #     f"--- Ended in %s seconds --- (Gas: {Web3.fromWei(gas_price, 'gwei')})"
            #     % (time.time() - start_time)
            # )

    def _scan_mempool_and_snipe(self) -> List[SnipingArbitrage]:
        """
        Watch the mempool for an arbitrageur targetting `arbitrage_path`
        Once detected, we snipe them by submitting a transaction with a higher gas price.
        """
        all_pending_txs = self.ethereum.w3_http.geth.txpool.content()["pending"]

        arbitrage: List[SnipingArbitrage] = []
        pending_tx_hashes = []
        for noob in self.noobs:
            if noob.address in all_pending_txs:
                for pending_tx in all_pending_txs[noob.address].values():
                    if pending_tx["hash"] not in self.last_txs:
                        arbitrage.append(
                            SnipingArbitrage(
                                pools=self._get_pools(pending_tx["input"]),
                                gas_price=int(pending_tx["gasPrice"], 16),
                                tx_hash=pending_tx["hash"],
                            )
                        )
                        pending_tx_hashes.append(pending_tx["hash"])

        if pending_tx_hashes:
            self.last_txs = pending_tx_hashes
        return arbitrage

    def _get_pools(self, contract_input: str) -> List[Pool]:
        """
        Split contract input into arguments and check each argument to see if it is a pool arg.
        Returns a list of Pool objects
        """
        pools: Set[Pool] = set()
        for arg in re.findall(".{%d}" % ARGUMENT_LENGTH, contract_input[2:]):
            address = f"0x{arg[2:42]}"
            if address in self.pools_by_address:
                pools.add(self.pools_by_address[address])

        return list(pools)
