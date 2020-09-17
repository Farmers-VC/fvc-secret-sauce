from services.exchange.uniswap import UniswapExchange
from services.pools.token import Token


class SushiSwapExchange(UniswapExchange):
    def calc_amount_out(self, token_in: Token, token_out: Token, amount_in_wei: int) -> int:
        """Calculate the amount out (in Wei) based on `amount_in` (in Wei). """
        amount_out_wei = super()._calc_amount_out(token_in, token_out, amount_in_wei)
        print(f'[SushiSwap] Exchange {token_in.from_wei(amount_in_wei)} {token_in.name} -> {token_out.from_wei(amount_out_wei)} {token_out.name}')
        return amount_out_wei
