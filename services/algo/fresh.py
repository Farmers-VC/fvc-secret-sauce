import time
from typing import Dict, List

from colored import fg, stylize
from web3 import Web3

from config import Config
from services.arbitrage.arbitrage import Arbitrage
from services.ethereum.ethereum import Ethereum
from services.notifications.notifications import Notification
from services.path.path import PathFinder
from services.pools.loader import PoolLoader
from services.printer.printer import PrinterContract
from services.ttypes.arbitrage import ArbitragePath
from services.utils import wait_new_block


class AlgoFresh:
    def __init__(
        self,
        ethereum: Ethereum,
        config: Config,
    ) -> None:
        self.ethereum = ethereum
        self.config = config
        self.pool_loader = PoolLoader(config=config)
        self.notification = Notification(self.config)
        self.printer = PrinterContract(self.ethereum, self.notification, self.config)
        self.arb_counter: Dict[str, int] = {}

    def _load_recent_arbitrage_path(self) -> List[ArbitragePath]:
        print("Fetching fresh pools and finding new arbitrage paths")
        pools = self.pool_loader.load_all_pools()
        path_finder = PathFinder(pools, self.config)
        arbitrage_paths = path_finder.find_all_paths()
        self.arbitrage = Arbitrage(pools, self.ethereum, self.config)
        print(
            stylize(
                f"Found {len(pools)} pools and {len(arbitrage_paths)} arbitrage paths..",
                fg("yellow"),
            )
        )
        return arbitrage_paths

    def arbitrage_fresh_pools(self):
        current_block = self.ethereum.w3.eth.blockNumber
        arbitrage_paths = self._load_recent_arbitrage_path()
        counter = 1
        while True:
            # Load again new pools Roughly every 40 minutes
            if counter % 200 == 0:
                arbitrage_paths = self._load_recent_arbitrage_path()
            latest_block = wait_new_block(self.ethereum, current_block)
            start_time = time.time()
            current_block = latest_block

            try:
                gas_price = self._calculate_gas_price()
            except Exception:
                gas_price = self.ethereum.w3.eth.gasPrice
            gas_price = int(gas_price * 1.5)
            positive_arbitrages = self.arbitrage.calc_arbitrage(
                arbitrage_paths, latest_block, gas_price
            )

            for positive_arb in positive_arbitrages:
                positive_arb_id = positive_arb.path_id
                num_consecutive_arb = self.arb_counter.get(positive_arb_id, 0)
                if num_consecutive_arb >= 2:
                    send_tx = self.config.send_tx
                else:
                    send_tx = False
                valid_arbitrage = self.printer.arbitrage_on_chain(
                    positive_arb,
                    latest_block,
                    send_tx=send_tx,
                    consecutive_arbs=num_consecutive_arb,
                )
                if valid_arbitrage and not send_tx:
                    self.arb_counter[positive_arb_id] = num_consecutive_arb + 1
                if valid_arbitrage and send_tx:
                    # If we find executed one arbitrage successfully, we reset everything to avoid sending tx to the same pools path
                    self.arb_counter = {}
                    break
                if not valid_arbitrage:
                    self.arb_counter[positive_arb_id] = 0

            counter += 1
            print(
                f"--- Ended in %s seconds --- (Gas: {Web3.fromWei(gas_price, 'gwei')})"
                % (time.time() - start_time)
            )
