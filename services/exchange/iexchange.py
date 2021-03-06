import abc

from web3.eth import Contract

from services.pools.token import Token
from config import Config


class ExchangeInterface(abc.ABC):
    @abc.abstractclassmethod
    def __init__(self, contract: Contract, config: Config) -> None:
        pass

    @abc.abstractclassmethod
    def calc_amount_out(
        self, token_in: Token, token_out: Token, amount_in_wei: int
    ) -> int:
        """Calculate the amount out (in Wei) based on `amount_in` (in Wei). """
        pass
