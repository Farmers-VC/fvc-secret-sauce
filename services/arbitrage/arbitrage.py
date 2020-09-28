from collections import defaultdict
from typing import Dict, List, Tuple

import numpy

from config import Config
from services.ethereum.ethereum import Ethereum
from services.exchange.factory import ExchangeFactory
from services.exchange.iexchange import ExchangeInterface
from services.notifications.notifications import Notification
from services.pools.pool import Pool
from services.pools.token import Token
from services.printer.printer import PrinterContract
from services.ttypes.arbitrage import ArbitragePath
from services.ttypes.block import Block


class Arbitrage:
    def __init__(self, pools: List[Pool], ethereum: Ethereum, config: Config) -> None:
        self.pools = pools
        self.ethereum = ethereum
        self.config = config
        self.notification = Notification(self.config)
        self.printer = PrinterContract(self.ethereum, self.notification, self.config)
        self.weth_address = self.config.get("WETH_ADDRESS").lower()
        self.weth_token = Token(name="WETH", address=self.weth_address, decimal=18)
        self.weth_amount_in_wei = self.weth_token.to_wei(self.config.min_amount)

        self.exchange_by_pool_address = self._init_all_exchange_contracts()

    def calc_arbitrage(
        self, arbitrage_paths: List[ArbitragePath], latest_block: Block, gas_price: int
    ):
        for arbitrage_path in arbitrage_paths:
            arbitrage_path.gas_price = gas_price
            _, all_amount_outs_wei = self._calculate_single_path_arbitrage(
                arbitrage_path, self.weth_amount_in_wei
            )
            arbitrage_path_fill = self._analyze_arbitrage(
                all_amount_outs_wei,
                arbitrage_path,
            )
            if arbitrage_path_fill:
                self.printer.arbitrage(arbitrage_path_fill, latest_block)

    # @timer
    def _calculate_gas_price(self) -> int:
        """Calculate the current gas price based on fast with high probability strategy"""
        gas_price = self.ethereum.w3.eth.generateGasPrice()
        if self.config.debug:
            print(f"Gas Price = {self.ethereum.w3.fromWei(gas_price, 'gwei')} Gwei")
        return gas_price

        # @timer

    def _analyze_arbitrage(
        self,
        all_amount_outs_wei: List[int],
        arbitrage_path: ArbitragePath,
    ) -> ArbitragePath:
        arbitrage_amount = (
            all_amount_outs_wei[-1]
            - self.weth_amount_in_wei
            - arbitrage_path.gas_price_execution
        )
        if arbitrage_amount > 0:
            arbitrage_path_fill = self._optimize_arbitrage_amount(
                arbitrage_path,
                arbitrage_amount,
            )
            return arbitrage_path_fill
        else:
            None

    def _optimize_arbitrage_amount(
        self,
        arbitrage_path: ArbitragePath,
        arbitrage_amount_wei: int,
    ) -> ArbitragePath:
        """After finding an arbitrage opportunity, maximize the gain by changing the amount in"""
        max_arbitrage_amount_wei = arbitrage_amount_wei
        optimal_amount_in_wei = self.weth_amount_in_wei
        min_amounts_by_weth_out: Dict[int, List[int]] = defaultdict(list)
        all_optimal_amount_out_wei = []
        for amount in numpy.arange(
            self.config.min_amount + self.config.get_float("INCREMENTAL_STEP"),
            self.config.max_amount,
            self.config.get_float("INCREMENTAL_STEP"),
        ):
            test_amount_in = self.weth_token.to_wei(amount)
            _, all_amount_outs_wei = self._calculate_single_path_arbitrage(
                arbitrage_path, test_amount_in
            )
            new_arbitrage_amount_wei = all_amount_outs_wei[-1] - test_amount_in
            min_amounts_by_weth_out[all_amount_outs_wei[-1]] = all_amount_outs_wei
            if self.config.debug:
                print(
                    f"[OPTIMIZATING][Amount in {self.weth_token.from_wei(test_amount_in)} ETH] Arbitrage: {self.weth_token.from_wei(new_arbitrage_amount_wei)} ETH"
                )

            if new_arbitrage_amount_wei >= max_arbitrage_amount_wei:
                max_arbitrage_amount_wei = new_arbitrage_amount_wei
                optimal_amount_in_wei = test_amount_in
                all_optimal_amount_out_wei = all_amount_outs_wei
            else:
                break

        for weth_out in sorted(min_amounts_by_weth_out):
            if weth_out > optimal_amount_in_wei + arbitrage_path.gas_price_execution:
                arbitrage_path.all_min_amount_out_wei = min_amounts_by_weth_out[
                    weth_out
                ]
                break

        arbitrage_path.max_arbitrage_amount_wei = max_arbitrage_amount_wei
        arbitrage_path.optimal_amount_in_wei = optimal_amount_in_wei
        arbitrage_path.all_optimal_amount_out_wei = all_optimal_amount_out_wei
        return arbitrage_path

    def _calculate_single_path_arbitrage(
        self, arbitrage_path: ArbitragePath, amount_in_wei: int
    ) -> Tuple[Token, List[int]]:
        all_amount_outs_wei: List[int] = []
        for connecting_path in arbitrage_path.connecting_paths:
            token_out, amount_out_wei = self._simulate_one_exchange(
                connecting_path.pool, connecting_path.token_in, amount_in_wei
            )
            all_amount_outs_wei.append(amount_out_wei)
            amount_in_wei = amount_out_wei
        return token_out, all_amount_outs_wei

    def _simulate_one_exchange(
        self, pool: Pool, token_in: Token, amount_in_wei: int
    ) -> Tuple[Token, int]:
        _, token_out = pool.get_token_pair_from_token_in(token_in.address)
        amount_out_wei = self.exchange_by_pool_address[pool.address].calc_amount_out(
            token_in, token_out, amount_in_wei
        )
        return token_out, amount_out_wei

    def _init_all_exchange_contracts(self) -> Dict[str, ExchangeInterface]:
        exchange_by_pool_address = {}
        for pool in self.pools:
            contract = self.ethereum.init_contract(pool)
            exchange = ExchangeFactory.create(
                contract, pool.type, debug=self.config.debug
            )
            exchange_by_pool_address[pool.address] = exchange
        return exchange_by_pool_address
