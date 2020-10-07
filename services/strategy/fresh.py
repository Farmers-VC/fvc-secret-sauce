import asyncio
import time
from typing import List

from colored import fg, stylize
from web3 import Web3

from config import Config
from services.arbitrage.arbitrage import Arbitrage
from services.ethereum.ethereum import Ethereum
from services.path.path import PathFinder
from services.pools.loader import PoolLoader
from services.ttypes.arbitrage import ArbitragePath
from services.utils import wait_new_block, calculate_gas_price


class StrategyFresh:
    def __init__(
        self,
        ethereum: Ethereum,
        config: Config,
    ) -> None:
        self.ethereum = ethereum
        self.config = config
        self.pool_loader = PoolLoader(config=config)

    def _load_recent_arbitrage_path(self) -> List[ArbitragePath]:
        try:
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
        except Exception as e:
            print("FUCK!", str(e))
            return self._load_recent_arbitrage_path()
        return arbitrage_paths

    # def arbitrage_fresh_pools(self):
    #     loop = asyncio.get_event_loop()
    #     loop.create_task(self.task(1))
    #     loop.create_task(self.task(2))

    #     loop.run_forever()
    #     loop.close()

    # async def task(self, thread):
    #     while True:
    #         current_block = self.ethereum.w3.eth.blockNumber
    #         print("TASK!", thread, current_block)
    #         await asyncio.sleep(1)

    def arbitrage_fresh_pools(self):
        loop = asyncio.get_event_loop()

        current_block = self.ethereum.w3.eth.blockNumber
        counter = 1
        breakpoint()
        while True:
            arbitrage_paths = self._load_recent_arbitrage_path()
            breakpoint()
            for index, chunk in enumerate(self._chunk(arbitrage_paths, 200)):
                print("START LOOP", index)
                loop.create_task(self.task(index, chunk))
        loop.run_forever()
        loop.close()

    async def task(self, thread, paths):
        print("STARTING THREAD: ", thread)
        while counter < 200:
            latest_block = wait_new_block(self.ethereum, current_block)
            start_time = time.time()
            current_block = latest_block

            try:
                gas_price = calculate_gas_price(self.ethereum, self.config)
            except Exception:
                print("Could not calculate gas price")
                gas_price = self.ethereum.w3.eth.gasPrice
            gas_price = int(gas_price * 1.5)
            self.arbitrage.calc_arbitrage_and_print(
                paths, latest_block, gas_price
            )

            counter += 1
            print(
                f"--- Ended in %s seconds --- (Gas: {Web3.fromWei(gas_price, 'gwei')})"
                % (time.time() - start_time)
            )

    def _chunk(paths, num_per_chunk):
        for i in range(0, len(paths), num_per_chunk):
            yield paths[i : i + num_per_chunk]
