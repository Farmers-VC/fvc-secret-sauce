from web3.eth import Contract

from services.exchange.iexchange import ExchangeInterface
from services.pools.token import Token


class UniswapExchange(ExchangeInterface):
    def __init__(self, contract: Contract, debug: bool = False) -> None:
        self.contract = contract
        self.swap_fee = 997
        self.debug = debug

    def calc_amount_out(
        self, token_in: Token, token_out: Token, amount_in_wei: int
    ) -> int:
        """Calculate the amount out (in Wei) based on `amount_in` (in Wei). """
        amount_out_wei = self._calc_amount_out(token_in, token_out, amount_in_wei)
        if self.debug:
            print(
                f"[Uniswap] Exchange {token_in.from_wei(amount_in_wei)} {token_in.name} -> {token_out.from_wei(amount_out_wei)} {token_out.name}"
            )
        return amount_out_wei

    def _calc_amount_out(
        self, token_in: Token, token_out: Token, amount_in_wei: int
    ) -> int:
        amount_in = token_in.from_wei(amount_in_wei)
        token_0 = self.contract.functions.token0().call()
        reserve_0, reserve_1, _ = self.contract.functions.getReserves().call()
        if token_0.lower() == token_in.address.lower():
            token_in_reserve = reserve_0
            token_out_reserve = reserve_1
        else:
            token_in_reserve = reserve_1
            token_out_reserve = reserve_0

        token_in_reserve = token_in.from_wei(token_in_reserve)
        token_out_reserve = token_out.from_wei(token_out_reserve)

        amount_in_with_fee = self.swap_fee * amount_in
        numerator = amount_in_with_fee * token_out_reserve
        denominator = (token_in_reserve * 1000) + amount_in_with_fee
        amount_out = numerator / denominator
        amount_out_wei = token_out.to_wei(amount_out)
        return amount_out_wei
