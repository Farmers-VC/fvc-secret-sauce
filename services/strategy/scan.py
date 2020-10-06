import time
from typing import List

from colored import fg, stylize
from web3 import Web3

from config import Config
from services.arbitrage.arbitrage import Arbitrage
from services.ethereum.ethereum import Ethereum
from services.path.path import PathFinder
from services.pools.pool import Pool
from services.ttypes.arbitrage import ArbitragePath
from services.utils import wait_new_block, calculate_gas_price


class StrategyScan:
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
                gas_price = calculate_gas_price(self.ethereum, self.config)
            except Exception:
                print("Could not calculate gas price")
                gas_price = self.ethereum.w3.eth.gasPrice
            gas_price = int(gas_price * 1.5)
            self.arbitrage.calc_arbitrage_and_print(
                arbitrage_paths, latest_block, gas_price
            )
            print(
                f"--- Ended in %s seconds --- (Gas: {Web3.fromWei(gas_price, 'gwei')})"
                % (time.time() - start_time)
            )
