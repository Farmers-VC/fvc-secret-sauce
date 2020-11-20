import time
from collections import defaultdict
import sys
from typing import Dict

from colored import fg, stylize

from config import Config
from services.arbitrage.arbitrage import Arbitrage
from services.ethereum.ethereum import Ethereum
from services.path.path import PathFinder
from services.pools.loader import PoolLoader
from services.ttypes.arbitrage import ArbitragePath
from services.utils import wait_new_block, calculate_gas_price, heartbeat


class StrategyWatcher:
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

    def _load_recent_arbitrage_path(self) -> Dict[str, Dict[str, ArbitragePath]]:
        try:
            start_time = time.time()
            sys.stdout.flush()
            pools = self.pool_loader.load_all_pools()
            path_finder = PathFinder(pools, self.config)
            paths_by_token = path_finder.find_all_paths_by_token()
            self.arbitrage = Arbitrage(
                pools, self.ethereum, self.config, consecutive=self.consecutive
            )
            print(
                f"Finish fetching pools & detecting paths (%s s)"
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
        return paths_by_token

    def watch(self):
        paths_by_token = self._load_recent_arbitrage_path()
        current_block = self.ethereum.w3.eth.blockNumber
        transfer_hash = self.ethereum.w3.keccak(
            text="Transfer(address,address,uint256)"
        ).hex()
        balancer_swap_hash = self.ethereum.w3.keccak(
            text="LOG_SWAP(address,address,address,uint256,uint256)"
        ).hex()
        transfer_filters = self.ethereum.w3.eth.filter(
            {"topics": [[balancer_swap_hash, transfer_hash]]}
        )
        while True:
            if current_block % 200 == 0:
                heartbeat(self.config)
                paths_by_token = self._load_recent_arbitrage_path()
            latest_block = wait_new_block(self.ethereum, current_block)
            current_block = latest_block
            start_time = time.time()
            addresses_by_tx_hash = defaultdict(set)  # TransactionHash => List[str]
            watcher_list = set()
            for event in transfer_filters.get_new_entries():
                if (
                    event["topics"][0].hex()
                    == "0x908fb5ee8f16c6bc9bc3690973819f32a4d4b10188134543c88706e0e1d43378"
                ):
                    # Balancer Event
                    for topic in event["topics"][1:]:
                        watcher_list.add(topic[12:].hex())
                else:
                    # Likely Uniswap
                    if event["address"] != self.config.get("WETH_ADDRESS"):
                        addresses_by_tx_hash[event["transactionHash"]].add(
                            event["address"].lower()
                        )
            if len(addresses_by_tx_hash) == 0 and len(watcher_list):
                continue
            for addresses in addresses_by_tx_hash.values():
                if len(addresses) > 1:
                    for addr in addresses:
                        watcher_list.add(addr)
            try:
                gas_price = calculate_gas_price(self.ethereum, self.config)
            except Exception:
                print("Could not calculate gas price")
                sys.stdout.flush()
                gas_price = self.ethereum.w3.eth.gasPrice

            gas_price = int(gas_price * self.config.gas_multiplier)
            for watcher in watcher_list:
                if watcher in paths_by_token:
                    paths = list(paths_by_token[watcher].values())
                    positive_arb = self.arbitrage.calc_arbitrage_and_print(
                        paths, latest_block, gas_price
                    )
                    if positive_arb and self.consecutive > 1:
                        self._focus_positive_arb(current_block, positive_arb, gas_price)
                        break

            print(
                f"--- {current_block} Ended in %s seconds --- (Gas: {self.ethereum.w3.fromWei(gas_price, 'gwei')})"
                % (time.time() - start_time)
            )
            sys.stdout.flush()

    def _focus_positive_arb(
        self, current_block: int, path: ArbitragePath, gas_price: int
    ) -> None:
        print(f"Focus on one Path until we find {self.consecutive} arbs")
        for _ in range(self.consecutive - 1):
            latest_block = wait_new_block(self.ethereum, current_block)
            current_block = latest_block
            if not self.arbitrage.calc_arbitrage_and_print(
                [path], latest_block, gas_price
            ):
                print("Could not find subsequent arbitrage")
                return
        return
