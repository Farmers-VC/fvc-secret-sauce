from typing import Dict, List

import yaml

from services.pools.pool import Pool
from services.pools.token import Token


class PoolLoader:
    @staticmethod
    def load_pools_yaml(token_path: str, pool_path: str) -> List[Pool]:
        tokens = _load_tokens_yaml(token_path)
        pools = _load_pools_yaml(pool_path, tokens)
        return pools


def _load_tokens_yaml(token_path: str) -> List[Token]:
    tokens: List[Token] = []
    with open(token_path, 'r') as stream:
        token_dict = yaml.safe_load(stream)
        for token_yaml in token_dict['tokens']:
            token = Token(name=token_yaml['name'], address=token_yaml['address'], decimal=token_yaml['decimal'])
            tokens.append(token)
    return tokens


def _load_pools_yaml(pool_path: str, tokens: List[Token]) -> List[Pool]:
    token_by_name: Dict[str, Token] = {token.name: token for token in tokens}

    pools: List[Pool] = []
    with open(pool_path, 'r') as stream:
        pools_dict = yaml.safe_load(stream)
        for pool_yaml in pools_dict['pools']:
            pool_tokens = [token_by_name[token_name] for token_name in pool_yaml['tokens']]
            pool = Pool(name=pool_yaml['name'], pool_type=pool_yaml['type'], address=pool_yaml['address'], tokens=pool_tokens)
            pools.append(pool)
    return pools
