from typing import List, Tuple

from services.pools.token import Token
from services.ttypes.contract import ContractTypeEnum


class Pool:
    def __init__(self, name: str, pool_type: str, address: str, tokens: List[Token]) -> None:
        self.name = name
        self.type = ContractTypeEnum[pool_type]
        self.address = address
        self.tokens = tokens

    @property
    def is_weth(self) -> bool:
        token_names = [token.name for token in self.tokens]
        return 'WETH' in token_names

    def contain_token(self, token_name: str) -> bool:
        for token in self.tokens:
            if token_name.lower() == token.name.lower():
                return True
        return False

    def get_token_pair_from_token_in(self, token_in_name: str) -> Tuple[Token, Token]:
        if not self.contain_token(token_in_name):
            raise Exception('Token in is not included in the token pair')

        if self.tokens[0].name.lower() == token_in_name.lower():
            return self.tokens[0], self.tokens[1]
        else:
            return self.tokens[1], self.tokens[0]
