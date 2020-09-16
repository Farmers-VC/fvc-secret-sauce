from decimal import Decimal

from web3 import Web3
from web3.eth import Contract

from services.exchange.iexchange import ExchangeInterface


class BalancerExchange(ExchangeInterface):
    def __init__(self, contract: Contract) -> None:
        self.contract = contract
        self.swap_fee = self.contract.functions.getSwapFee().call()

    def calc_amount_out(self, token_in: str, token_out: str, amount_in: str) -> str:
        """Calculate the current amount out based on `amount_in`"""
        token_in_balance = self.contract.functions.getBalance(token_in).call()
        token_out_balance = self.contract.functions.getBalance(token_out).call()
        token_in_denormalized_weight = self.contract.functions.getDenormalizedWeight(token_in).call()
        token_out_denormalized_weight = self.contract.functions.getDenormalizedWeight(token_out).call()
        amount_in_decimal = Web3.toWei(Decimal(amount_in), 'ether')
        amount_out = self.contract.functions.calcOutGivenIn(token_in_balance, token_in_denormalized_weight, token_out_balance, token_out_denormalized_weight, amount_in_decimal, self.swap_fee).call()
        return amount_out
