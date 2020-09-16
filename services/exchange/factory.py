from web3.eth import Contract

from services.exchange.balancer import BalancerExchange
from services.exchange.iexchange import ExchangeInterface
from services.exchange.uniswap import UniswapExchange
from services.ttypes.contract import ContractTypeEnum


class ExchangeFactory:
    @staticmethod
    def create(contract: Contract, contract_type: ContractTypeEnum) -> ExchangeInterface:
        if contract_type == ContractTypeEnum.BPOOL:
            return BalancerExchange(contract)
        if contract_type == ContractTypeEnum.UNISWAP:
            return UniswapExchange(contract)
        raise Exception('Exchange not supported.')
