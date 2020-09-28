from typing import List

from config import Config
from services.ethereum.ethereum import Ethereum
from services.pools.pool import Pool
from services.ttypes.sniper import SnipingNoob
from services.utils import init_all_exchange_contracts, wait_new_block

# from services


class AlgoSnipe:
    def __init__(
        self, ethereum: Ethereum, config: Config, pools: List[Pool], noobs: SnipingNoob
    ) -> None:
        self.ethereum = ethereum
        self.config = config
        self.pools_by_address = {pool.address: pool for pool in pools}
        self.noobs = noobs
        self.exchange_by_pool_address = init_all_exchange_contracts(
            self.ethereum, pools, self.config
        )
        # self.sniper =

    def snipe_arbitrageur(self) -> None:
        print("-----------------------------------------------------------")
        print("----------------- SNIPING SOME NOOOOOBS -------------------")
        print("-----------------------------------------------------------")

        current_block_number = self.ethereum.w3.eth.blockNumber
        while True:
            latest_block = wait_new_block(self.ethereum, current_block_number)
            current_block_number = latest_block.number
            start_time = time.time()
            try:
                gas_price = self._calculate_gas_price()
            except Exception:
                gas_price = self.ethereum.w3.eth.gasPrice
