from collections import defaultdict
from typing import Dict, List

from config import Config
from services.pools.pool import Pool
from services.pools.token import Token
from services.ttypes.arbitrage import ArbitragePath, ConnectingPath


class PathFinder:
    def __init__(self, pools: List[Pool], config: Config) -> None:
        self.config = config
        self.num_pools = len(pools)
        self.pools_by_token: Dict[str, List[Pool]] = defaultdict(list)
        for pool in pools:
            for token in pool.tokens:
                self.pools_by_token[token.address.lower()].append(pool)
        self.weth_address = self.config.get("WETH_ADDRESS").lower()

    def find_all_paths(self) -> List[ArbitragePath]:
        all_arbitrage_paths: List[ArbitragePath] = []
        existing_paths = set()
        for weth_pool in self.pools_by_token[self.weth_address]:
            token_in, token_out = weth_pool.get_token_pair_from_token_in(
                self.weth_address
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
                arb_path = ArbitragePath(connecting_paths=combined_path)
                if arb_path.path_id in existing_paths:
                    continue
                all_arbitrage_paths.append(arb_path)
                existing_paths.add(arb_path.path_id)
        for path in all_arbitrage_paths:
            path.print_path()
        print(
            f"Out of {self.num_pools} pools (Uniswap/Balancer/Sushiswap), PathFinder detected {len(all_arbitrage_paths)} paths:"
        )
        return all_arbitrage_paths

    def find_all_paths_by_token(self) -> Dict[str, Dict[str, ArbitragePath]]:
        paths_by_token_addr: Dict[str, Dict[str, ArbitragePath]] = {}
        arb_paths = self.find_all_paths()
        for path in arb_paths:
            for token_path in path.connecting_paths:
                paths_by_token_addr[token_path.token_in.address] = {path.path_id: path}
                paths_by_token_addr[token_path.token_out.address] = {path.path_id: path}
        return paths_by_token_addr

    def _find_connecting_paths(
        self, step: int, token_in: Token, previous_pool: Pool = None
    ) -> List[List[ConnectingPath]]:
        """Given a Token in, find all connecting paths from the list of all Pools avaivable"""
        if token_in.address == self.weth_address or step > self.config.get_int(
            "MAX_STEP_SUPPORTED"
        ):
            # Means that we're already returning a WETH or we're about `MAX_STEP_SUPPORTED`
            return []
        all_connecting_paths: List[List[ConnectingPath]] = []
        end_weth_path_found = False
        for pool in self.pools_by_token[token_in.address]:
            _, token_out = pool.get_token_pair_from_token_in(token_in.address)
            if (previous_pool and pool.address == previous_pool.address) or (
                step == self.config.get_int("MAX_STEP_SUPPORTED")
                and token_out.address != self.weth_address
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

        if (
            step == self.config.get_int("MAX_STEP_SUPPORTED")
            and end_weth_path_found is False
        ):
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
