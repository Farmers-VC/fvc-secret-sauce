from web3 import Web3
from web3.eth import Contract

from services.exchange.iexchange import ExchangeInterface


class UniswapExchange(ExchangeInterface):
    def __init__(self, contract: Contract) -> None:
        self.contract = contract
        self.swap_fee = 997

    def calc_amount_out(self, token_in: str, token_out: str, amount_in: str) -> str:
        """Calculate the current amount out based on `amount_in`"""
        amount_in = int(amount_in)
        token_0 = self.contract.functions.token0().call()
        reserve_0, reserve_1, _ = self.contract.functions.getReserves().call()
        if token_0.lower() == token_in.lower():
            token_in_reserve = reserve_0
            token_out_reserve = reserve_1
        else:
            token_in_reserve = reserve_1
            token_out_reserve = reserve_0

        token_in_reserve = Web3.fromWei(token_in_reserve, 'ether')
        token_out_reserve = Web3.fromWei(token_out_reserve, 'ether')

        amount_in_with_fee = self.swap_fee * amount_in
        numerator = amount_in_with_fee * token_out_reserve
        denominator = (token_in_reserve * 1000) + amount_in_with_fee
        amount_out = numerator / denominator
        return amount_out
