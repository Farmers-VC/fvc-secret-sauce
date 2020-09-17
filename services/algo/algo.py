import random
import time
from typing import Dict, List

from colored import fg, stylize
from web3 import Web3

from services.ethereum.ethereum import Ethereum
from services.exchange.factory import ExchangeFactory
from services.exchange.iexchange import ExchangeInterface
from services.pools.pool import Pool
from services.twilio.twilio import TwilioService


class Algo:
    def __init__(self, pools: List[Pool], w3: Web3) -> None:
        self.pools = pools
        self.w3 = w3
        self.exchange_by_pool_address = self._init_all_exchange_contracts()
        self.weth_pools = [pool for pool in self.pools if pool.is_weth]
        self.non_weth_pools = [pool for pool in self.pools if not pool.is_weth]
        self.twilio = TwilioService()

    def _init_all_exchange_contracts(self) -> Dict[str, ExchangeInterface]:
        exchange_by_pool_address = {}
        for pool in self.pools:
            eth_svc = Ethereum(w3=self.w3)
            contract = eth_svc.init_contract(pool)
            exchange = ExchangeFactory.create(contract, pool.type)
            exchange_by_pool_address[pool.address] = exchange
        return exchange_by_pool_address

    def find_arbitrage(self) -> None:
        while True:
            time.sleep(0.5)
            rand_eth = str(random.uniform(1.0, 25.0))
            WETH_AMOUNT_IN = Web3.toWei(rand_eth, 'ether')
            for weth_pool_1 in self.weth_pools:
                print('----------------------- NEW PATH ------------------------')
                token_in_1, token_out_1 = weth_pool_1.get_token_pair_from_token_in('WETH')
                amount_out_wei_1 = self.exchange_by_pool_address[weth_pool_1.address].calc_amount_out(token_in_1, token_out_1, WETH_AMOUNT_IN)
                for mix_pool_2 in self.weth_pools + self.non_weth_pools:
                    if mix_pool_2.contain_token(token_out_1.name):
                        token_in_2, token_out_2 = mix_pool_2.get_token_pair_from_token_in(token_out_1.name)
                        print(">> ", end = '')
                        amount_out_wei_2 = self.exchange_by_pool_address[mix_pool_2.address].calc_amount_out(token_in_2, token_out_2, amount_out_wei_1)
                        if token_out_2.name != 'WETH':
                            for weth_pool_3 in self.weth_pools:
                                if weth_pool_3.contain_token(token_out_2.name):
                                    token_in_3, token_out_3 = weth_pool_3.get_token_pair_from_token_in(token_out_2.name)
                                    print(">>>> ", end = '')
                                    amount_out_wei_3 = self.exchange_by_pool_address[weth_pool_3.address].calc_amount_out(token_in_3, token_out_3, amount_out_wei_2)
                                    if token_out_3.name != 'WETH':
                                        raise Exception('Last exchange should results in WETH.')
                                    arbitrage_amount = token_out_3.from_wei(amount_out_wei_3 - WETH_AMOUNT_IN)
                                    if arbitrage_amount > 0:
                                        print(stylize(f'Arbitrage: {arbitrage_amount}', fg('green')))
                                    else:
                                        print(stylize(f'Arbitrage: {arbitrage_amount}', fg('red')))
                                    if amount_out_wei_3 > (WETH_AMOUNT_IN + Web3.toWei(0.2, 'ether')):
                                        print('-----------------------------------------------------------')
                                        print('------------------- ARBITRAGE DETECTED --------------------')
                                        print('-----------------------------------------------------------')
                                        self.twilio.send_message(f'Arbitrage Opportunity: +{arbitrage_amount} ETH')

    # def one_exchange(self, steps: int) -> None:
