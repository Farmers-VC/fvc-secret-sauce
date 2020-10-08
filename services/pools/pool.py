from typing import List, Tuple

from services.pools.token import Token
from services.ttypes.contract import ContractTypeEnum


class Pool:
    def __init__(
        self, name: str, pool_type: str, address: str, tokens: List[Token]
    ) -> None:
        self.name = name
        self.type = ContractTypeEnum[pool_type]
        self.address = address.lower()
        self.tokens = tokens

    @property
    def is_weth(self) -> bool:
        token_names = [token.name for token in self.tokens]
        return "WETH" in token_names

    @property
    def router_address(self) -> str:
        if self.type == ContractTypeEnum.UNISWAP:
            return "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
        if self.type == ContractTypeEnum.SUSHISWAP:
            return "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"
        return None

    def contain_token_name(self, token_name: str) -> bool:
        for token in self.tokens:
            if token_name.lower() == token.name.lower():
                return True
        return False

    def contain_token(self, token_address: str) -> bool:
        for token in self.tokens:
            if token_address.lower() == token.address.lower():
                return True
        return False

    def get_token_pair_from_token_in(
        self, token_in_address: str
    ) -> Tuple[Token, Token]:
        if not self.contain_token(token_in_address):
            raise Exception(
                f"Token {token_in_address} in is not included in the token pair"
            )

        if self.tokens[0].address.lower() == token_in_address.lower():
            return self.tokens[0], self.tokens[1]
        else:
            return self.tokens[1], self.tokens[0]
