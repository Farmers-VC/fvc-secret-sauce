# import threading
import time
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy
from colored import fg, stylize
from web3 import Web3

from services.ethereum.ethereum import Ethereum
from services.exchange.factory import ExchangeFactory
from services.exchange.iexchange import ExchangeInterface
from services.pools.pool import Pool
from services.pools.token import Token
from services.ttypes.arbitrage import ArbitragePath, ConnectingPath
from services.twilio.twilio import TwilioService

MAX_STEP_SUPPORTED = 3
WETH_AMOUNT_IN = Web3.toWei("1.0", "ether")
ORIGIN_TOKEN_IN = "WETH"


class Algo:
    def __init__(self, pools: List[Pool], w3: Web3) -> None:
        self.pools = pools
        self.w3 = w3
        self.exchange_by_pool_address = self._init_all_exchange_contracts()
        self.pools_by_token: Dict[str, List[Pool]] = defaultdict(list)
        for pool in self.pools:
            for token in pool.tokens:
                self.pools_by_token[token.name].append(pool)
        self.twilio = TwilioService()

    def _init_all_exchange_contracts(self) -> Dict[str, ExchangeInterface]:
        exchange_by_pool_address = {}
        for pool in self.pools:
            eth_svc = Ethereum(w3=self.w3)
            contract = eth_svc.init_contract(pool)
            exchange = ExchangeFactory.create(contract, pool.type)
            exchange_by_pool_address[pool.address] = exchange
        return exchange_by_pool_address

    def _safety_checks(self, step: int, token_in: Token, token_out: Token) -> None:
        if step == 1 and token_in.name != "WETH":
            raise Exception("Only support entry with WETH")
        if step == 2 and token_in.name == "WETH":
            raise Exception("Step 2 should never be WETH as a token_in")
        if step == 3 and token_in.name == "WETH":
            raise Exception("Step 3 should never be WETH as a token_in")
        if step == MAX_STEP_SUPPORTED and token_out.name != "WETH":
            raise Exception("Last step should always result in WETH")
        if step > MAX_STEP_SUPPORTED:
            raise Exception("We only supported MAX_STEP_SUPPORTED")

    def _analyze_arbitrage(
        self,
        original_amount_in_wei: int,
        amount_out_wei: int,
        token_out: Token,
        arbitrage_path: ArbitragePath,
        iteration=0,
    ) -> None:
        if token_out.name == "WETH":
            arbitrage_amount = token_out.from_wei(
                amount_out_wei - original_amount_in_wei
            )
            if arbitrage_amount > 0:
                # print("-----------------------------------------------------------")
                # print("------------------- ARBITRAGE DETECTED --------------------")
                # print("-----------------------------------------------------------")
                (
                    optimal_amount_in,
                    optimal_arbitrage_amount,
                ) = self._optimize_arbitrage_amount(
                    arbitrage_path, original_amount_in_wei, arbitrage_amount, token_out
                )
                paths = arbitrage_path.connecting_paths[0].token_in.name
                for path in arbitrage_path.connecting_paths:
                    paths += f" -> {path.token_out.name}"

                result_str = f"Arbitrage [{paths}]: +{optimal_arbitrage_amount} ETH (Amount in: {token_out.from_wei(optimal_amount_in)} ETH)"
                print(
                    stylize(
                        result_str,
                        fg("green"),
                    )
                )
                if optimal_arbitrage_amount > 0.1:
                    self.twilio.send_message(result_str)
            # else:
            #     print(stylize(f"Arbitrage: {arbitrage_amount}", fg("red")))

        else:
            raise Exception("Token out is not WETH")

    def _optimize_arbitrage_amount(
        self,
        arbitrage_path: ArbitragePath,
        amount_in_wei: int,
        arbitrage_amount: int,
        token_out: Token,
    ) -> Tuple[int, int]:
        """After finding an arbitrage opportunity, maximize the gain by changing the amount in"""
        max_arbitrage_amount = arbitrage_amount
        optimal_amount_in = amount_in_wei
        # print("---OPTIMIZING ARBITRAGE---")
        for amount in numpy.arange(1.1, 30, 0.10):
            test_amount_in = token_out.to_wei(amount)
            _, amount_out_wei = self._calculate_single_path_arbitrage(
                arbitrage_path, test_amount_in
            )
            new_arbitrage_amount = token_out.from_wei(amount_out_wei - test_amount_in)
            # print(
            #     f"[Amount in {token_out.from_wei(test_amount_in)} ETH] Arbitrage: {new_arbitrage_amount} ETH"
            # )
            if new_arbitrage_amount >= max_arbitrage_amount:
                max_arbitrage_amount = new_arbitrage_amount
                optimal_amount_in = test_amount_in
            else:
                break
        return optimal_amount_in, max_arbitrage_amount

    def _find_connecting_paths(
        self, step: int, token_in: Token, previous_pool: Pool = None
    ) -> List[List[ConnectingPath]]:
        """Given a Token in, find all connecting paths from the list of all Pools avaivable"""
        if token_in.name == "WETH" or step > MAX_STEP_SUPPORTED:
            # Means that we're already returning a WETH or we're about `MAX_STEP_SUPPORTED`
            return []
        all_connecting_paths: List[List[ConnectingPath]] = []
        end_weth_path_found = False
        for pool in self.pools_by_token[token_in.name]:
            _, token_out = pool.get_token_pair_from_token_in(token_in.name)
            if (previous_pool and pool.address == previous_pool.address) or (
                step == MAX_STEP_SUPPORTED and token_out.name != "WETH"
            ):
                continue

            end_weth_path_found = True
            self._safety_checks(step, token_in, token_out)
            connecting_paths: List[List[ConnectingPath]] = self._find_connecting_paths(
                step + 1, token_out, pool
            )
            if connecting_paths is None:
                # Means that no end path with WETH has been found - Invalid Path
                continue
            all_connecting_paths += self._combine_paths(
                ConnectingPath(pool=pool, token_in=token_in, token_out=token_out),
                connecting_paths,
            )

        if step == MAX_STEP_SUPPORTED and end_weth_path_found is False:
            return None
        return all_connecting_paths

    def _combine_paths(
        self, origin_path: ConnectingPath, available_paths: List[List[ConnectingPath]]
    ) -> List[List[ConnectingPath]]:
        combined_paths: List[List[ConnectingPath]] = []
        if len(available_paths) == 0:
            return [[origin_path]]
        for available_path in available_paths:
            combined_paths.append([origin_path] + available_path)
        return combined_paths

    def find_all_paths(self) -> List[ArbitragePath]:
        all_arbitrage_paths: List[ArbitragePath] = []
        for weth_pool in self.pools_by_token[ORIGIN_TOKEN_IN]:
            token_in, token_out = weth_pool.get_token_pair_from_token_in(
                ORIGIN_TOKEN_IN
            )
            self._safety_checks(
                1,
                token_in,
                token_out,
            )
            connecting_paths: List[List[ConnectingPath]] = self._find_connecting_paths(
                2, token_out, weth_pool
            )
            if connecting_paths is None or len(connecting_paths) == 0:
                # Means that no end path with WETH has been found - Invalid Path
                continue
            combined_paths: List[List[ConnectingPath]] = self._combine_paths(
                ConnectingPath(pool=weth_pool, token_in=token_in, token_out=token_out),
                connecting_paths,
            )
            for combined_path in combined_paths:
                all_arbitrage_paths.append(
                    ArbitragePath(connecting_paths=combined_path)
                )
        return all_arbitrage_paths

    def scan_arbitrage(self):
        arbitrage_paths: List[ArbitragePath] = self.find_all_paths()

        while True:
            for arbitrage_path in arbitrage_paths:
                token_out, amount_out_wei = self._calculate_single_path_arbitrage(
                    arbitrage_path, WETH_AMOUNT_IN
                )
                self._analyze_arbitrage(
                    WETH_AMOUNT_IN, amount_out_wei, token_out, arbitrage_path
                )
            time.sleep(5)

    def _calculate_single_path_arbitrage(
        self, arbitrage_path: ArbitragePath, amount_in_wei: int
    ) -> Tuple[Token, int]:
        for connecting_path in arbitrage_path.connecting_paths:
            token_out, amount_out_wei = self._simulate_one_exchange(
                connecting_path.pool, connecting_path.token_in, amount_in_wei
            )
            if token_out.name.lower() != connecting_path.token_out.name.lower():
                raise Exception("Token out problem")
            amount_in_wei = amount_out_wei
        return token_out, amount_out_wei

    def _simulate_one_exchange(
        self, pool: Pool, token_in: Token, amount_in_wei: int
    ) -> Tuple[Token, int]:
        _, token_out = pool.get_token_pair_from_token_in(token_in.name)
        amount_out_wei = self.exchange_by_pool_address[pool.address].calc_amount_out(
            token_in, token_out, amount_in_wei
        )
        return token_out, amount_out_wei
