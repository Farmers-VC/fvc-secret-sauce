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

        amount_in_with_fee = self.swap_fee * amount_in
        numerator = amount_in_with_fee * token_out_reserve
        denominator = (token_in_reserve * 1000) + amount_in_with_fee
        amount_out = numerator / denominator
        # slippage = self._calc_price_impact(amount_in, amount_out, token_in_reserve, token_out_reserve)
        return amount_out
#             const inputReserve = this.reserveOf(inputAmount.token)
#     const outputReserve = this.reserveOf(inputAmount.token.equals(this.token0) ? this.token1 : this.token0)
#     const inputAmountWithFee = JSBI.multiply(inputAmount.raw, _997)
#     const numerator = JSBI.multiply(inputAmountWithFee, outputReserve.raw)
#     const denominator = JSBI.add(JSBI.multiply(inputReserve.raw, _1000), inputAmountWithFee)
#     const outputAmount = new TokenAmount(
#       inputAmount.token.equals(this.token0) ? this.token1 : this.token0,
#       JSBI.divide(numerator, denominator)
#     )
#     if (JSBI.equal(outputAmount.raw, ZERO)) {
#       throw new InsufficientInputAmountError()
#     }


    # def _calc_price_impact(self, amount_in: int, amount_out_without_slippage: int, token_in_reserve: int, token_out_reserve: int) -> float:
    #     mid_price = (token_out_reserve / token_in_reserve)
    #     exact_quote = mid_price * amount_in
    #     slippage = (exact_quote - amount_out_without_slippage) / exact_quote
    #     breakpoint()
    #     return slippage


# function computePriceImpact(midPrice: Price, inputAmount: CurrencyAmount, outputAmount: CurrencyAmount): Percent {
#   const exactQuote = midPrice.raw.multiply(inputAmount.raw)
#   // calculate slippage := (exactQuote - outputAmount) / exactQuote
#   const slippage = exactQuote.subtract(outputAmount.raw).divide(exactQuote)
#   return new Percent(slippage.numerator, slippage.denominator)
# }
