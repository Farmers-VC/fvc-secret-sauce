# import threading
import time
from typing import Dict, List, Tuple

import numpy
from colored import fg, stylize

from config import Config
from services.ethereum.ethereum import Ethereum
from services.exchange.factory import ExchangeFactory
from services.exchange.iexchange import ExchangeInterface
from services.notifications.notifications import Notification
from services.path.path import PathFinder
from services.pools.pool import Pool
from services.pools.token import Token
from services.printer.printer import PrinterContract
from services.ttypes.arbitrage import ArbitragePath


class Algo:
    def __init__(
        self,
        pools: List[Pool],
        ethereum: Ethereum,
        config: Config,
        max_amount_in_weth: float = 3.0,
    ) -> None:
        self.pools = pools
        self.ethereum = ethereum
        self.config = config
        self.weth_address = self.config.get("WETH_ADDRESS").lower()
        self.max_amount_in_weth = max_amount_in_weth

        self.exchange_by_pool_address = self._init_all_exchange_contracts()
        self.notification = Notification(self.config)
        self.printer = PrinterContract(self.ethereum, self.notification, self.config)
        self.path_finder = PathFinder(self.pools, self.config)

    def scan_arbitrage(self):
        print("-----------------------------------------------------------")
        print("----------------- WELCOME TO FARMERS VC -------------------")
        print("-----------------------------------------------------------")
        print(f"Scanning for arbitrage paths....")
        arbitrage_paths: List[ArbitragePath] = self.path_finder.find_all_paths()
        print(stylize(f"Found {len(arbitrage_paths)} arbitrage paths..", fg("yellow")))
        while True:
            start_time = time.time()
            for arbitrage_path in arbitrage_paths:
                token_out, all_amount_outs_wei = self._calculate_single_path_arbitrage(
                    arbitrage_path, self.config.get_int("WETH_AMOUNT_IN")
                )
                self._analyze_arbitrage(
                    self.config.get_int("WETH_AMOUNT_IN"),
                    all_amount_outs_wei,
                    token_out,
                    arbitrage_path,
                )
            print("--- Ended in %s seconds ---" % (time.time() - start_time))
            if self.config.kovan:
                time.sleep(10)

    def _init_all_exchange_contracts(self) -> Dict[str, ExchangeInterface]:
        exchange_by_pool_address = {}
        for pool in self.pools:
            contract = self.ethereum.init_contract(pool)
            exchange = ExchangeFactory.create(
                contract, pool.type, debug=self.config.debug
            )
            exchange_by_pool_address[pool.address] = exchange
        return exchange_by_pool_address

    def _safety_checks(self, step: int, token_in: Token, token_out: Token) -> None:
        if step == 1 and token_in.address != self.weth_address:
            raise Exception("Only support entry with WETH")
        if (
            step == self.config.get_int("MAX_STEP_SUPPORTED")
            and token_out.address != self.weth_address
        ):
            raise Exception("Last step should always result in WETH")
        if step > self.config.get_int("MAX_STEP_SUPPORTED"):
            raise Exception(
                f"We only supporte {self.config.get_int('MAX_STEP_SUPPORTED')} steps"
            )

    def _analyze_arbitrage(
        self,
        original_amount_in_wei: int,
        all_amount_outs_wei: List[int],
        token_out: Token,
        arbitrage_path: ArbitragePath,
        iteration=0,
    ) -> None:
        if token_out.address == self.weth_address:
            arbitrage_amount = token_out.from_wei(
                all_amount_outs_wei[-1] - original_amount_in_wei
            )
            if arbitrage_amount > 0.03:
                (
                    optimal_amount_in,
                    max_arbitrage_amount,
                ) = self._optimize_arbitrage_amount(
                    arbitrage_path, original_amount_in_wei, arbitrage_amount, token_out
                )
                if max_arbitrage_amount > 0.20:
                    self.printer.arbitrage(
                        arbitrage_path,
                        optimal_amount_in,
                        max_arbitrage_amount,
                        all_amount_outs_wei,
                    )
        else:
            raise Exception("Token out is not WETH")

    def _optimize_arbitrage_amount(
        self,
        arbitrage_path: ArbitragePath,
        amount_in_wei: int,
        arbitrage_amount: int,
        token_out: Token,
    ) -> Tuple[int, int, int]:
        """After finding an arbitrage opportunity, maximize the gain by changing the amount in"""
        max_arbitrage_amount = arbitrage_amount
        optimal_amount_in = amount_in_wei
        for amount in numpy.arange(
            1.1, self.max_amount_in_weth, self.config.get_float("INCREMENTAL_STEP")
        ):
            test_amount_in = token_out.to_wei(amount)
            _, all_amount_outs_wei = self._calculate_single_path_arbitrage(
                arbitrage_path, test_amount_in
            )
            new_arbitrage_amount = token_out.from_wei(
                all_amount_outs_wei[-1] - test_amount_in
            )
            if self.config.debug:
                print(
                    f"[OPTIMIZATING][Amount in {token_out.from_wei(test_amount_in)} ETH] Arbitrage: {new_arbitrage_amount} ETH"
                )
            if new_arbitrage_amount >= max_arbitrage_amount:
                max_arbitrage_amount = new_arbitrage_amount
                optimal_amount_in = test_amount_in
            else:
                break
        return optimal_amount_in, max_arbitrage_amount

    def _calculate_single_path_arbitrage(
        self, arbitrage_path: ArbitragePath, amount_in_wei: int
    ) -> Tuple[Token, List[int]]:
        all_amount_outs_wei: List[int] = []
        for connecting_path in arbitrage_path.connecting_paths:
            token_out, amount_out_wei = self._simulate_one_exchange(
                connecting_path.pool, connecting_path.token_in, amount_in_wei
            )
            if token_out.address.lower() != connecting_path.token_out.address.lower():
                raise Exception("Token out problem")
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
