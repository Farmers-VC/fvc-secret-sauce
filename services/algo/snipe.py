import time
from typing import List

from web3 import Web3

from config import Config
from services.arbitrage.arbitrage import Arbitrage
from services.ethereum.ethereum import Ethereum
from services.path.path import PathFinder
from services.pools.pool import Pool
from services.strategy.sniper import Sniper
from services.ttypes.arbitrage import ArbitragePath
from services.ttypes.sniper import SnipingArbitrage, SnipingNoob
from services.utils import wait_new_block


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

    def snipe_arbitrageur(self) -> None:
        print("-----------------------------------------------------------")
        print("----------------- SNIPING SOME NOOOOOBS -------------------")
        print("-----------------------------------------------------------")

        current_block_number = self.ethereum.w3.eth.blockNumber
        while True:
            latest_block = wait_new_block(self.ethereum, current_block_number)
            current_block_number = latest_block.number
            start_time = time.time()
            sniping_arbitrages: List[
                SnipingArbitrage
            ] = self.sniper.scan_mempool_and_snipe()
            for sniping_arbitrage in sniping_arbitrages:
                path_finder = PathFinder(sniping_arbitrage.pools, self.config)
                arbitrage_paths: List[ArbitragePath] = path_finder.find_all_paths()
                if arbitrage_paths and self.config.debug:
                    print("Found {len(arbitrage_paths)} paths")
                self.arbitrage.calc_arbitrage(
                    arbitrage_paths, latest_block, sniping_arbitrage.gas_price + 1
                )

            gas_price = sniping_arbitrages[-1].gas_price if sniping_arbitrages else 0
            print(
                f"--- Ended in %s seconds --- (Gas: {Web3.fromWei(gas_price, 'gwei')})"
                % (time.time() - start_time)
            )
