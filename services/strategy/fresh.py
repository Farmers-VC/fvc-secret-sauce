import asyncio
import aiohttp

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


    def arbitrage_fresh_pools(self):
        breakpoint()
        while True:
            arbitrage_paths = self._load_recent_arbitrage_path()
            print("FOUND PATHS:", len(arbitrage_paths))

            asyncio.run(self._queue_tasks(arbitrage_paths))


    async def _queue_tasks(self, arbitrage_paths):
        print("QUEUE TASKS")
        async with aiohttp.ClientSession() as session:
            coroutines = [self._task(index, chunk) for index, chunk in enumerate(self._chunk(arbitrage_paths, 10))]
            pending_tasks = set(
                [asyncio.create_task(coro) for coro in coroutines]
            )
        while pending_tasks:
            done_tasks, pending_tasks = await asyncio.wait(pending_tasks,  return_when=asyncio.ALL_COMPLETED)
        print("ALL TASKS COMPLETED")

    async def _task(self, thread, paths):
        print("STARTING THREAD: ", thread)

        counter = 1
        current_block = await self.ethereum.w3.eth.blockNumber


        while counter < 200:
            print("COUNTER", thread, counter)
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
                gas_price = self.ethereum.w3.eth.gasPrice
            gas_price = int(gas_price * 1.5)

            self.arbitrage.calc_arbitrage_and_print(
                paths, latest_block, gas_price
            )

            counter += 1
            print(
                f"{thread}--- Ended in %s seconds --- (Gas: {Web3.fromWei(gas_price, 'gwei')})"
                % (time.time() - start_time)
            )
            await asyncio.sleep(0.01)


    def _chunk(self, paths, num_per_chunk):
        for i in range(0, len(paths), num_per_chunk):
            yield paths[i : i + num_per_chunk]


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
            print(
                stylize(
                    f"Exception loading arbitrage path: {str(e)}",
                    fg("red"),
                )
            )
            return self._load_recent_arbitrage_path()
        return arbitrage_paths
