from web3.eth import Contract

from services.exchange.balancer import BalancerExchange
from services.exchange.iexchange import ExchangeInterface
from services.exchange.uniswap import UniswapExchange
from services.ttypes.contract import ContractTypeEnum
from config import Config


class ExchangeFactory:
    @staticmethod
    def create(
        contract: Contract, contract_type: ContractTypeEnum, config: Config
    ) -> ExchangeInterface:
        if contract_type == ContractTypeEnum.BPOOL:
            return BalancerExchange(contract, config)
        if contract_type == ContractTypeEnum.UNISWAP:
            return UniswapExchange(contract, config)
        if contract_type == ContractTypeEnum.SUSHISWAP:
            return UniswapExchange(contract, config)
        raise Exception("Exchange not supported.")
