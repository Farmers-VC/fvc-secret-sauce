import sys

from web3.eth import Contract

from services.exchange.iexchange import ExchangeInterface
from services.pools.token import Token
from config import Config


class BalancerExchange(ExchangeInterface):
    def __init__(self, contract: Contract, config: Config) -> None:
        self.contract = contract
        self.config = config
        self.swap_fee = self.contract.functions.getSwapFee().call(
            block_identifier=self.config.since
        )

    def calc_amount_out(
        self, token_in: Token, token_out: Token, amount_in_wei: int
    ) -> int:
        """Calculate the amount out (in Wei) based on `amount_in` (in Wei). """
        token_in_balance = self.contract.functions.getBalance(
            token_in.checksum_address
        ).call(block_identifier=self.config.since)
        token_out_balance = self.contract.functions.getBalance(
            token_out.checksum_address
        ).call(block_identifier=self.config.since)
        token_in_denormalized_weight = self.contract.functions.getDenormalizedWeight(
            token_in.checksum_address
        ).call(block_identifier=self.config.since)
        token_out_denormalized_weight = self.contract.functions.getDenormalizedWeight(
            token_out.checksum_address
        ).call(block_identifier=self.config.since)
        amount_out_wei = self.contract.functions.calcOutGivenIn(
            token_in_balance,
            token_in_denormalized_weight,
            token_out_balance,
            token_out_denormalized_weight,
            amount_in_wei,
            self.swap_fee,
        ).call(block_identifier=self.config.since)
        if self.config.debug:
            print(
                f"[BPOOL] Exchange {token_in.from_wei(amount_in_wei)} {token_in.name} -> {token_out.from_wei(amount_out_wei)} {token_out.name}"
            )
            sys.stdout.flush()

        return amount_out_wei

    def calc_amount_out_proxy(
        self, token_in: Token, token_out: Token, amount_in_wei: int
    ) -> int:
        pass
