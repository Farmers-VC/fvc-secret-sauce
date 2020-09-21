from typing import Dict, List

import requests
import yaml

from services.pools.pool import Pool
from services.pools.token import Token


class PoolLoader:
    @staticmethod
    def load_uniswap_pools() -> List[Pool]:
        # https://thegraph.com/explorer/subgraph/uniswap/uniswap-v2?selected=playground
        query = """
        {
            pairs(
                first: 1000, 
                where: {
                    reserveUSD_gt: 50000, 
                    volumeUSD_gt: 10000
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

    @staticmethod
    def load_balancer_pools() -> List[Pool]:
        # https://thegraph.com/explorer/subgraph/balancer-labs/balancer
        query = """
        {
            pools(
                first: 1000, 
                where: {
                    publicSwap: true, 
                    tokensCount:2, 
                    liquidity_gt: 50000, 
                    totalSwapVolume_gt:10000
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

    @staticmethod
    def load_pools_yaml(token_path: str, pool_path: str) -> List[Pool]:
        tokens = _load_tokens_yaml(token_path)
        pools = _load_pools_yaml(pool_path, tokens)
        return pools


def _load_tokens_yaml(token_path: str) -> List[Token]:
    tokens: List[Token] = []
    with open(token_path, "r") as stream:
        token_dict = yaml.safe_load(stream)
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
