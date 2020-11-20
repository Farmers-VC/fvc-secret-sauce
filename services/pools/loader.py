from typing import Dict, List

import requests
import yaml
import sys

from config import Config
from services.pools.pool import Pool
from services.pools.token import Token


class PoolLoader:
    def __init__(self, config: Config):
        self.config = config

    def load_all_pools(self) -> List[Pool]:
        print("Loading Uniswap, Balancer, SushiSwap and others pools ...")
        sys.stdout.flush()

        if self.config.kovan:
            return self._load_pools_yaml()

        uniswap_pools = []
        balancer_pools = []

        min_max_liq = (
            [(self.config.min_liquidity, self.config.max_liquidity)]
            if self.config.min_liquidity and self.config.max_liquidity
            else [
                (5000, 10000),
                (10001, 20000),
                (20001, 50000),
                (50001, 100000),
                (100001, 500000),
                (500001, 2000000),
                (2000001, 5000000),
                (5000000, 20000000),
                (20000001, 500000000),
            ]
        )

        for (min_liq, max_liq) in min_max_liq:
            uniswap_pools += self._load_uniswap_pools(min_liq, max_liq)
            balancer_pools += self._load_balancer_pools(min_liq, max_liq)
        sushiswap_pools = []  # self._load_sushiswap_pools()

        yaml_pools = self._load_pools_yaml()
        all_pools = uniswap_pools + balancer_pools + sushiswap_pools + yaml_pools
        pools_with_only_tokens = self._filter_only_tokens(all_pools)
        pools_without_blacklist = self._filter_blacklist_pools(pools_with_only_tokens)
        return pools_without_blacklist

    def _filter_only_tokens(self, pools: List[Pool]) -> List[Pool]:
        if not self.config.only_tokens:
            return pools
        filtered_pools: List[Pool] = []
        for pool in pools:
            for token_name in self.config.only_tokens:
                if pool.contain_token_name(token_name):
                    filtered_pools.append(pool)
                    continue
        return filtered_pools

    def _filter_blacklist_pools(self, pools: List[Pool]) -> List[Pool]:
        blacklist_tokens = self._load_tokens_yaml(
            self.config.get("TOKEN_BLACKLIST_YAML_PATH")
        )
        blacklist_addresses = [token.address.lower() for token in blacklist_tokens]

        filtered_pools: List[Pool] = []
        for pool in pools:
            blacklist_token_found = False
            for blacklist_addr in blacklist_addresses:
                if pool.contain_token(blacklist_addr):
                    blacklist_token_found = True
                    break
            if not blacklist_token_found:
                filtered_pools.append(pool)

        return filtered_pools

    def _load_uniswap_pools(self, min_liquidity: int, max_liquidity: int) -> List[Pool]:
        # https://thegraph.com/explorer/subgraph/uniswap/uniswap-v2?selected=playground
        query = f"""
            {{
                pairs(
                    first: 1000,
                    where: {{
                        reserveUSD_lt: {max_liquidity},
                        reserveUSD_gt: {min_liquidity},
                    }},
                    orderBy: volumeUSD,
                    orderDirection: desc){{
                    id
                    token0 {{
                      id
                      name
                      symbol
                      decimals
                    }}
                    token1 {{
                      id
                      name
                      symbol
                      decimals
                    }}
                }}
            }}
        """
        url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
        resp = requests.post(url, json={"query": query})
        pairs = resp.json()["data"]["pairs"]
        pools: List[Pool] = []
        for pair in pairs:
            pools.append(
                Pool(
                    name=f"{pair['token0']['symbol']}/{pair['token1']['symbol']}",
                    pool_type="UNISWAP",
                    address=pair["id"],
                    tokens=[
                        Token(
                            name=pair["token0"]["symbol"],
                            address=pair["token0"]["id"],
                            decimal=int(pair["token0"]["decimals"]),
                        ),
                        Token(
                            name=pair["token1"]["symbol"],
                            address=pair["token1"]["id"],
                            decimal=int(pair["token1"]["decimals"]),
                        ),
                    ],
                )
            )
        return pools

    def _load_sushiswap_pools(self) -> List[Pool]:
        # https://thegraph.com/explorer/subgraph/dmihal/sushiswap
        query = f"""
        {{
            pairs(
                first: 1000,
                orderBy: volumeUSD,
                orderDirection: desc){{
                id
                token0 {{
                  id
                  name
                  symbol
                  decimals
                }}
                token1 {{
                  id
                  name
                  symbol
                  decimals
                }}
            }}
        }}
        """
        url = "https://api.thegraph.com/subgraphs/name/dmihal/sushiswap"
        resp = requests.post(url, json={"query": query})
        pairs = resp.json()["data"]["pairs"]
        pools: List[Pool] = []
        for pair in pairs:
            pools.append(
                Pool(
                    name=f"{pair['token0']['symbol']}/{pair['token1']['symbol']}",
                    pool_type="SUSHISWAP",
                    address=pair["id"],
                    tokens=[
                        Token(
                            name=pair["token0"]["symbol"],
                            address=pair["token0"]["id"],
                            decimal=int(pair["token0"]["decimals"]),
                        ),
                        Token(
                            name=pair["token1"]["symbol"],
                            address=pair["token1"]["id"],
                            decimal=int(pair["token1"]["decimals"]),
                        ),
                    ],
                )
            )
        return pools

    def _load_balancer_pools(
        self,
        min_liquidity: int,
        max_liquidity: int,
    ) -> List[Pool]:
        # https://thegraph.com/explorer/subgraph/balancer-labs/balancer
        query = f"""
            {{
                pools(
                    first: 1000,
                    where: {{
                        publicSwap: true,
                        tokensCount:2,
                        liquidity_lt: {max_liquidity},
                        liquidity_gt: {min_liquidity},
                    }},
                    orderBy: totalSwapVolume,
                    orderDirection: desc
                ) {{
                    id
                    tokens {{
                      address
                      decimals
                      symbol
                    }}
                }}
            }}
        """
        url = "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer"
        resp = requests.post(url, json={"query": query})
        pairs = resp.json()["data"]["pools"]
        pools: List[Pool] = []
        for pair in pairs:
            pools.append(
                Pool(
                    name=f"{pair['tokens'][0]['symbol']}/{pair['tokens'][1]['symbol']}",
                    pool_type="BPOOL",
                    address=pair["id"],
                    tokens=[
                        Token(
                            name=pair["tokens"][0]["symbol"],
                            address=pair["tokens"][0]["address"],
                            decimal=int(pair["tokens"][0]["decimals"]),
                        ),
                        Token(
                            name=pair["tokens"][1]["symbol"],
                            address=pair["tokens"][1]["address"],
                            decimal=int(pair["tokens"][1]["decimals"]),
                        ),
                    ],
                )
            )
        return pools

    def _load_pools_yaml(self) -> List[Pool]:
        tokens = self._load_tokens_yaml(self.config.get("TOKEN_YAML_PATH"))
        token_by_name: Dict[str, Token] = {token.name: token for token in tokens}
        pools: List[Pool] = []
        with open(self.config.get("POOL_YAML_PATH"), "r") as stream:
            pools_dict = yaml.safe_load(stream)
            if pools_dict["pools"]:
                for pool_yaml in pools_dict["pools"]:
                    pool_tokens = [
                        token_by_name[token_name] for token_name in pool_yaml["tokens"]
                    ]
                    pool = Pool(
                        name=pool_yaml["name"],
                        pool_type=pool_yaml["type"],
                        address=pool_yaml["address"],
                        tokens=pool_tokens,
                    )
                    pools.append(pool)

        return pools

    def _load_tokens_yaml(self, token_path: str) -> List[Token]:
        tokens: List[Token] = []
        with open(token_path, "r") as stream:
            token_dict = yaml.safe_load(stream)
            if token_dict["tokens"]:
                for token_yaml in token_dict["tokens"]:
                    token = Token(
                        name=token_yaml["name"],
                        address=token_yaml["address"],
                        decimal=token_yaml["decimal"],
                    )
                    tokens.append(token)
        return tokens
