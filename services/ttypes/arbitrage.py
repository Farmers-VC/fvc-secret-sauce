from dataclasses import dataclass, field
from typing import List

from web3 import Web3

from config import Config, FIXED_TOKEN_PATH_SIZE, FIXED_ADDRESSES_PER_TOKEN_PATH
from services.pools.pool import Pool
from services.pools.token import Token
from services.ttypes.contract import ContractTypeEnum
from services.utils import mask_address, fill_zero_addresses

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
    all_optimal_amount_out_wei: List[int] = field(default_factory=list)
    all_min_amount_out_wei: List[int] = field(default_factory=list)
    gas_price: int = None
    max_arbitrage_amount_wei: int = None
    max_block_height: int = None

    @property
    def path_id(self) -> str:
        path_concat = "".join([path.pool.address for path in self.connecting_paths])
        return path_concat

    def contain_token(self, token_address: str) -> bool:
        for path in self.connecting_paths:
            if path.pool.contain_token(token_address):
                return True
        return False

    @property
    def pool_types(self) -> List[int]:
        pool_types = []
        for i, path in enumerate(self.connecting_paths):
            if path.pool.type == ContractTypeEnum.BPOOL:
                pool_types.append(ContractTypeEnum.BPOOL.value)
            if path.pool.type == ContractTypeEnum.UNISWAP and (
                i >= len(self.connecting_paths) - 1
                or self.connecting_paths[i + 1].pool.type != ContractTypeEnum.UNISWAP
            ):
                pool_types.append(ContractTypeEnum.UNISWAP.value)
            if path.pool.type == ContractTypeEnum.SUSHISWAP and (
                i >= len(self.connecting_paths) - 1
                or self.connecting_paths[i + 1].pool.type != ContractTypeEnum.SUSHISWAP
            ):
                # Sushiswap uses the same int value as Uniswap
                pool_types.append(ContractTypeEnum.UNISWAP.value)
        # Fill in with 8 that maps to nothing
        pool_types = pool_types + [
            8 for _ in range(FIXED_TOKEN_PATH_SIZE - len(pool_types))
        ]
        return pool_types

    @property
    def all_min_amount_out_wei_grouped(self) -> List[str]:
        """Group min amounts per consecutive ContractTypeEnum (only take the last one)"""
        all_min_amount_grouped = []
        for i, path in enumerate(self.connecting_paths):
            if path.pool.type == ContractTypeEnum.BPOOL:
                all_min_amount_grouped.append(self.all_min_amount_out_wei[i])
            if path.pool.type == ContractTypeEnum.UNISWAP and (
                i >= len(self.connecting_paths) - 1
                or self.connecting_paths[i + 1].pool.type != ContractTypeEnum.UNISWAP
            ):
                all_min_amount_grouped.append(self.all_min_amount_out_wei[i])
            if path.pool.type == ContractTypeEnum.SUSHISWAP and (
                i >= len(self.connecting_paths) - 1
                or self.connecting_paths[i + 1].pool.type != ContractTypeEnum.SUSHISWAP
            ):
                # Sushiswap uses the same int value as Uniswap
                all_min_amount_grouped.append(self.all_min_amount_out_wei[i])
        # Fill in with 9999999999999000000000000000000 for useless min_amount
        all_min_amount_grouped = all_min_amount_grouped + [
            9999999999999000000000000000000
            for _ in range(FIXED_TOKEN_PATH_SIZE - len(all_min_amount_grouped))
        ]
        return all_min_amount_grouped

    @property
    def token_out(self) -> Token:
        return self.connecting_paths[-1].token_out

    @property
    def gas_price_execution(self) -> int:
        return self.gas_price * ESTIMATE_GAS_EXECUTION

    @property
    def token_paths(self) -> List[List[str]]:
        token_paths = []
        uniswap_token_paths = []
        sushiswap_token_paths = []
        for i, path in enumerate(self.connecting_paths):
            if path.pool.type == ContractTypeEnum.BPOOL:
                bpool_path = fill_zero_addresses(
                    [
                        mask_address(path.pool.address),
                        mask_address(path.token_in.address),
                        mask_address(path.token_out.address),
                    ],
                    FIXED_ADDRESSES_PER_TOKEN_PATH - 3,
                )
                token_paths.append(bpool_path)
            if path.pool.type == ContractTypeEnum.UNISWAP:
                uniswap_token_paths.append(mask_address(path.token_in.address))
                if (
                    i >= (len(self.connecting_paths) - 1)
                    or self.connecting_paths[i + 1].pool.type
                    != ContractTypeEnum.UNISWAP
                ):
                    uniswap_token_paths.append(mask_address(path.token_out.address))
                    num_tokens = len(uniswap_token_paths)
                    # -2 because last item is total number of `num_tokens` and second to last is the Router addres
                    uniswap_token_paths = fill_zero_addresses(
                        uniswap_token_paths,
                        FIXED_ADDRESSES_PER_TOKEN_PATH - num_tokens - 2,
                    )
                    uniswap_token_paths = uniswap_token_paths + [
                        path.pool.router_address,
                        f"0x000000000000000000000000000000000000000{num_tokens}",
                    ]
                    token_paths.append(uniswap_token_paths)
                    uniswap_token_paths = []
            if path.pool.type == ContractTypeEnum.SUSHISWAP:
                sushiswap_token_paths.append(mask_address(path.token_in.address))
                if (
                    i >= (len(self.connecting_paths) - 1)
                    or self.connecting_paths[i + 1].pool.type
                    != ContractTypeEnum.SUSHISWAP
                ):
                    sushiswap_token_paths.append(mask_address(path.token_out.address))
                    num_tokens = len(sushiswap_token_paths)
                    sushiswap_token_paths = fill_zero_addresses(
                        sushiswap_token_paths,
                        FIXED_ADDRESSES_PER_TOKEN_PATH - num_tokens - 2,
                    )
                    sushiswap_token_paths = sushiswap_token_paths + [
                        path.pool.router_address,
                        f"0x000000000000000000000000000000000000000{num_tokens}",
                    ]
                    token_paths.append(sushiswap_token_paths)
                    sushiswap_token_paths = []
        token_paths = token_paths + [
            fill_zero_addresses([], FIXED_ADDRESSES_PER_TOKEN_PATH)
            for _ in range(FIXED_TOKEN_PATH_SIZE - len(token_paths))
        ]
        return token_paths

    @property
    def tx_remix_str(self) -> str:
        return f"{self.token_paths},{self.all_min_amount_out_wei_grouped},{self.optimal_amount_in_wei},{self.gas_price_execution},{self.pool_types},{self.max_block_height}\n\n".replace(
            "'", '"'
        )

    def print(
        self, latest_block: int, tx_hash: str = "", consecutive_arbs: int = None
    ) -> str:
        paths = f"{self.connecting_paths[0].token_in.from_wei(self.optimal_amount_in_wei)} {self.connecting_paths[0].token_in.name} ({self.connecting_paths[0].pool.type.name})"
        for idx, path in enumerate(self.connecting_paths):
            path_token_out = path.token_out
            paths += f" -> {path_token_out.from_wei(self.all_optimal_amount_out_wei[idx])} {path_token_out.name} ({path.pool.type.name})"
        beers = self.display_emoji_by_amount(":beer:")
        arbitrage_result = f"{beers}\nOpportunity: *{self.token_out.from_wei(self.max_arbitrage_amount_wei)}* ETH :moneybag:\nPath: {paths} \nAmount in: {self.token_out.from_wei(self.optimal_amount_in_wei)} ETH\nGas Price: {Web3.fromWei(self.gas_price, 'gwei')} Gwei\nGas Execution: {self.token_out.from_wei(self.gas_price_execution)} ETH\nCurrent Block: {latest_block} (Max: {self.max_block_height})\nMin Amount out: {[str(item) for item in self.all_min_amount_out_wei]}\n"
        if tx_hash:
            arbitrage_result = (
                arbitrage_result + f"Tx hash: https://etherscan.io/tx/{tx_hash}\n"
            )
        if consecutive_arbs:
            arbitrage_result = (
                arbitrage_result + f"Consecutive Arbitrage: {consecutive_arbs}\n"
            )

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
