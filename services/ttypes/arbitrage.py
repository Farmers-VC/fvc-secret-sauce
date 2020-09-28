from dataclasses import dataclass
from typing import List, Set

from web3 import Web3

from config import Config
from services.pools.pool import Pool
from services.pools.token import Token
from services.ttypes.block import Block

config = Config()
MAX_STEP_SUPPORTED = config.get_int("MAX_STEP_SUPPORTED")
ESTIMATE_GAS_EXECUTION = config.get_int("ESTIMATE_GAS_EXECUTION")


@dataclass
class ConnectingPath:
    pool: Pool
    token_in: Token
    token_out: Token


@dataclass
class ArbitragePath:
    connecting_paths: List[ConnectingPath]
    optimal_amount_in_wei: int = None
    all_optimal_amount_out_wei: List[int] = None
    all_min_amount_out_wei: List[int] = None
    gas_price: int = None
    max_arbitrage_amount_wei: int = None
    max_block_height: int = None

    def contain_token(self, token_address: str) -> bool:
        for path in self.connecting_paths:
            if path.pool.contain_token(token_address):
                return True
        return False

    @property
    def pool_and_token_addresses(self) -> Set[str]:
        addresses: Set[str] = set()
        for path in self.connecting_paths:
            addresses.add(path.token_in.address)
            addresses.add(path.token_out.address)
            addresses.add(path.pool.address)
        return addresses

    @property
    def pool_paths(self) -> List[str]:
        return [
            Web3.toChecksumAddress(path.pool.address) for path in self.connecting_paths
        ]

    @property
    def pool_types(self) -> List[int]:
        return [path.pool.type.value for path in self.connecting_paths]

    @property
    def token_out(self) -> Token:
        return self.connecting_paths[-1].token_out

    @property
    def gas_price_execution(self) -> int:
        return self.gas_price * ESTIMATE_GAS_EXECUTION

    @property
    def tx_remix_str(self) -> str:
        contract_path_input = []
        contract_type_input = []
        for path in self.connecting_paths:
            contract_path_input.append(path.pool.address)
            contract_type_input.append(str(path.pool.type.value))
        return f"{contract_path_input},{contract_type_input},{[str(item) for item in self.all_min_amount_out_wei]},{self.optimal_amount_in_wei},{self.gas_price_execution},{self.max_block_height}\n\n".replace(
            "'", '"'
        )

    def print(self, block: Block) -> str:
        paths = f"{self.connecting_paths[0].token_in.from_wei(self.optimal_amount_in_wei)} {self.connecting_paths[0].token_in.name} ({self.connecting_paths[0].pool.type.name})"
        for idx, path in enumerate(self.connecting_paths):
            path_token_out = path.token_out
            paths += f" -> {path_token_out.from_wei(self.all_optimal_amount_out_wei[idx])} {path_token_out.name} ({path.pool.type.name})"
        beers = self.display_emoji_by_amount(":beer:")
        arbitrage_result = f"{beers}\nOpportunity: *{self.token_out.from_wei(self.max_arbitrage_amount_wei)}* ETH :moneybag:\nPath: {paths} \nAmount in: {self.token_out.from_wei(self.optimal_amount_in_wei)} ETH\nGas Price: {Web3.fromWei(self.gas_price, 'gwei')} Gwei\nCurrent Block: {block.number} (Max: {self.max_block_height}) (Timestamp: {block.timestamp})\n"

        arbitrage_result = arbitrage_result + self.tx_remix_str
        return arbitrage_result

    def display_emoji_by_amount(self, emoji: str) -> str:
        max_arbitrage_amount = self.token_out.from_wei(self.max_arbitrage_amount_wei)
        times = 1
        if max_arbitrage_amount > 0.5 and max_arbitrage_amount < 1.0:
            times = 2
        if max_arbitrage_amount >= 1.0 and max_arbitrage_amount < 1.5:
            times = 5
        if max_arbitrage_amount >= 1.5 and max_arbitrage_amount < 2.0:
            times = 10
        if max_arbitrage_amount >= 2.0:
            times = 20
        return "".join([emoji for _ in range(times)])
