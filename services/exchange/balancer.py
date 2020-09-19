# from decimal import Decimal

# from web3 import Web3
from web3.eth import Contract

from services.exchange.iexchange import ExchangeInterface
from services.pools.token import Token


class BalancerExchange(ExchangeInterface):
    def __init__(self, contract: Contract) -> None:
        self.contract = contract
        self.swap_fee = self.contract.functions.getSwapFee().call()

    def calc_amount_out(
        self, token_in: Token, token_out: Token, amount_in_wei: int
    ) -> int:
        """Calculate the amount out (in Wei) based on `amount_in` (in Wei). """
        token_in_balance = self.contract.functions.getBalance(token_in.address).call()
        token_out_balance = self.contract.functions.getBalance(token_out.address).call()
        token_in_denormalized_weight = self.contract.functions.getDenormalizedWeight(
            token_in.address
        ).call()
        token_out_denormalized_weight = self.contract.functions.getDenormalizedWeight(
            token_out.address
        ).call()
        amount_out_wei = self.contract.functions.calcOutGivenIn(
            token_in_balance,
            token_in_denormalized_weight,
            token_out_balance,
            token_out_denormalized_weight,
            amount_in_wei,
            self.swap_fee,
        ).call()
        # print(
        #     f"[BPOOL] Exchange {token_in.from_wei(amount_in_wei)} {token_in.name} -> {token_out.from_wei(amount_out_wei)} {token_out.name}"
        # )
        return amount_out_wei

    def calc_amount_out_proxy(
        self, token_in: Token, token_out: Token, amount_in_wei: int
    ) -> int:
        pass
