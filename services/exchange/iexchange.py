import abc

from web3.eth import Contract


class ExchangeInterface(abc.ABC):
    @abc.abstractclassmethod
    def __init__(self, contract: Contract) -> None:
        pass

    @abc.abstractclassmethod
    def calc_amount_out(self, token_in: str, token_out: str, amount_in: str) -> str:
        pass
