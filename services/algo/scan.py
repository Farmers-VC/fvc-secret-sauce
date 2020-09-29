import time
from typing import List

from colored import fg, stylize
from web3 import Web3

from config import Config
from services.arbitrage.arbitrage import Arbitrage
from services.ethereum.ethereum import Ethereum
from services.notifications.notifications import Notification
from services.path.path import PathFinder
from services.pools.pool import Pool
from services.printer.printer import PrinterContract
from services.ttypes.arbitrage import ArbitragePath
from services.utils import wait_new_block


class AlgoScan:
    def __init__(
        self,
        pools: List[Pool],
        ethereum: Ethereum,
        config: Config,
    ) -> None:
        self.pools = pools
        self.ethereum = ethereum
        self.config = config
        self.arbitrage = Arbitrage(self.pools, self.ethereum, self.config)
        self.path_finder = PathFinder(self.pools, self.config)
        self.notification = Notification(self.config)
        self.printer = PrinterContract(self.ethereum, self.notification, self.config)

    def scan_arbitrage(self):
        print(f"Scanning for arbitrage paths....")
        arbitrage_paths: List[ArbitragePath] = self.path_finder.find_all_paths()
        print(
            stylize(
                f"Found {len(self.pools)} pools and {len(arbitrage_paths)} arbitrage paths..",
                fg("yellow"),
            )
        )
        current_block = self.ethereum.w3.eth.blockNumber
        while True:
            latest_block = wait_new_block(self.ethereum, current_block)
            current_block = latest_block
            start_time = time.time()

            try:
                gas_price = self._calculate_gas_price()
            except Exception:
                gas_price = self.ethereum.w3.eth.gasPrice
            gas_price = int(gas_price * 1.5)
            positive_arbitrages = self.arbitrage.calc_arbitrage(
                arbitrage_paths, latest_block, gas_price
            )

            for positive_arb in positive_arbitrages:
                print(positive_arb.print(latest_block))
                self.printer.arbitrage_on_chain(
                    positive_arb, latest_block, send_tx=False
                )
            print(
                f"--- Ended in %s seconds --- (Gas: {Web3.fromWei(gas_price, 'gwei')})"
                % (time.time() - start_time)
            )
