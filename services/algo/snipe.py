from typing import List

from config import Config
from services.arbitrage.arbitrage import Arbitrage
from services.ethereum.ethereum import Ethereum
from services.notifications.notifications import Notification
from services.path.path import PathFinder
from services.pools.pool import Pool
from services.printer.printer import PrinterContract
from services.strategy.sniper import Sniper
from services.ttypes.arbitrage import ArbitragePath
from services.ttypes.sniper import SnipingArbitrage, SnipingNoob


class AlgoSnipe:
    def __init__(
        self, ethereum: Ethereum, config: Config, pools: List[Pool], noobs: SnipingNoob
    ) -> None:
        self.ethereum = ethereum
        self.config = config
        self.pools_by_address = {pool.address: pool for pool in pools}
        self.noobs = noobs
        self.sniper = Sniper(
            self.ethereum, self.config, self.noobs, self.pools_by_address
        )
        self.arbitrage = Arbitrage(pools, self.ethereum, self.config)
        self.notification = Notification(self.config)
        self.printer = PrinterContract(self.ethereum, self.notification, self.config)

    def snipe_arbitrageur(self) -> None:
        while True:
            latest_block = self.ethereum.w3.eth.blockNumber
            # start_time = time.time()
            sniping_arbitrages: List[
                SnipingArbitrage
            ] = self.sniper.scan_mempool_and_snipe()
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
