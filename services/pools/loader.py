from typing import Dict, List

import requests
import yaml

from config import Config
from services.pools.pool import Pool
from services.pools.token import Token


class PoolLoader:
    def __init__(self, config: Config):
        self.config = config

    def load_all_pools(self) -> List[Pool]:
        if self.config.kovan:
            return self._load_pools_yaml()

        uniswap_pools = self._load_uniswap_pools()
        balancer_pools = self._load_balancer_pools()

        yaml_pools = self._load_pools_yaml()
        pools_without_blacklist = self._filter_blacklist_pools(
            uniswap_pools + balancer_pools + yaml_pools
        )

        return pools_without_blacklist

    def _filter_blacklist_pools(self, pools: List[Pool]) -> List[Pool]:
        blacklist_tokens = _load_tokens_yaml(
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

    def _load_uniswap_pools(self) -> List[Pool]:
        # https://thegraph.com/explorer/subgraph/uniswap/uniswap-v2?selected=playground
        query = """
        {
            pairs(
                first: 1000,
                where: {
                    reserveUSD_lt: 900000,
                    reserveUSD_gt: 30000,
                },
                orderBy: volumeUSD,
                orderDirection: desc){
                id
                token0 {
                  id
                  name
                  symbol
                  decimals
                }
                token1 {
                  id
                  name
                  symbol
                  decimals
                }
            }
        }
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

    def _load_balancer_pools(self) -> List[Pool]:
        # https://thegraph.com/explorer/subgraph/balancer-labs/balancer
        query = """
        {
            pools(
                first: 1000,
                where: {
                    publicSwap: true,
                    tokensCount:2,
                    liquidity_lt: 900000,
                    liquidity_gt: 30000,
                },
                orderBy: totalSwapVolume,
                orderDirection: desc) {
                id
                tokens {
                  address
                  decimals
                  symbol
                }
            }
        }

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
        tokens = _load_tokens_yaml(self.config.get("TOKEN_YAML_PATH"))
        pools = _load_pools_yaml(self.config.get("POOL_YAML_PATH"), tokens)
        return pools


def _load_tokens_yaml(token_path: str) -> List[Token]:
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


def _load_pools_yaml(pool_path: str, tokens: List[Token]) -> List[Pool]:
    token_by_name: Dict[str, Token] = {token.name: token for token in tokens}

    pools: List[Pool] = []
    with open(pool_path, "r") as stream:
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
