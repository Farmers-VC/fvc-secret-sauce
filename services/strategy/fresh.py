import time
import sys
from typing import List

from colored import fg, stylize
from web3 import Web3

from config import Config
from services.arbitrage.arbitrage import Arbitrage
from services.ethereum.ethereum import Ethereum
from services.path.path import PathFinder
from services.pools.loader import PoolLoader
from services.ttypes.arbitrage import ArbitragePath
from services.utils import wait_new_block, calculate_gas_price, heartbeat


class StrategyFresh:
    def __init__(
        self,
        consecutive: int,
        ethereum: Ethereum,
        config: Config,
    ) -> None:
        self.consecutive = consecutive
        self.ethereum = ethereum
        self.config = config
        self.pool_loader = PoolLoader(config=config)

    def _load_recent_arbitrage_path(self) -> List[ArbitragePath]:
        try:
            start_time = time.time()
            sys.stdout.flush()
            pools = self.pool_loader.load_all_pools()
            path_finder = PathFinder(pools, self.config)
            arbitrage_paths = path_finder.find_all_paths()
            self.arbitrage = Arbitrage(
                pools, self.ethereum, self.config, consecutive=self.consecutive
            )
            print(
                f"Finish fetching pools & detecting paths (%s)"
                % (time.time() - start_time)
            )
            sys.stdout.flush()
        except Exception as e:
            print(
                stylize(
                    f"Exception loading arbitrage path: {str(e)}",
                    fg("red"),
                )
            )
            sys.stdout.flush()
            return self._load_recent_arbitrage_path()
        return arbitrage_paths

    def arbitrage_fresh_pools(self):
        current_block = self.ethereum.w3.eth.blockNumber
        arbitrage_paths = self._load_recent_arbitrage_path()
        counter = 1
        while True:
            # Load again new pools Roughly every 40 minutes
            if counter % 200 == 0:
                arbitrage_paths = self._load_recent_arbitrage_path()
                heartbeat(self.config)
            latest_block = wait_new_block(self.ethereum, current_block)
            start_time = time.time()
            current_block = latest_block

            try:
                gas_price = calculate_gas_price(self.ethereum, self.config)
            except Exception as e:
                print(
                    stylize(
                        f"Could not calculate gas price {str(e)}",
                        fg("red"),
                    )
                )
                sys.stdout.flush()
                gas_price = self.ethereum.w3.eth.gasPrice
            gas_price = max(
                [int(gas_price * self.config.gas_multiplier), Web3.toWei(121, "gwei")]
            )
            self.arbitrage.calc_arbitrage_and_print(
                arbitrage_paths, latest_block, gas_price
            )

            counter += 1
            print(
                f"--- Ended in %s seconds --- (Gas: {Web3.fromWei(gas_price, 'gwei')})"
                % (time.time() - start_time)
            )
            sys.stdout.flush()
