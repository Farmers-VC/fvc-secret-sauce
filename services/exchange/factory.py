from web3.eth import Contract

from services.exchange.balancer import BalancerExchange
from services.exchange.balancer_proxy import BalancerProxyExchange
from services.exchange.iexchange import ExchangeInterface
from services.exchange.sushiswap import SushiSwapExchange
from services.exchange.uniswap import UniswapExchange
from services.ttypes.contract import ContractTypeEnum


class ExchangeFactory:
    @staticmethod
    def create(
        contract: Contract, contract_type: ContractTypeEnum, debug: bool = False
    ) -> ExchangeInterface:
        if contract_type == ContractTypeEnum.BPOOL:
            return BalancerExchange(contract, debug)
        if contract_type == ContractTypeEnum.UNISWAP:
            return UniswapExchange(contract, debug)
        if contract_type == ContractTypeEnum.SUSHISWAP:
            return SushiSwapExchange(contract, debug)
        if contract_type == ContractTypeEnum.BALANCER_PROXY:
            return BalancerProxyExchange(contract, debug)
        raise Exception("Exchange not supported.")
