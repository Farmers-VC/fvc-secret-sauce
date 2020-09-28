import time
from typing import Dict, List

from config import Config
from services.ethereum.ethereum import Ethereum
from services.exchange.factory import ExchangeFactory
from services.exchange.iexchange import ExchangeInterface
from services.pools.pool import Pool
from services.ttypes.block import Block


def timer(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if "log_time" in kw:
            name = kw.get("log_name", method.__name__.upper())
            kw["log_time"][name] = int((te - ts) * 1000)
        else:
            print(f"{method.__name__} {(te - ts) * 1000} ms")
        return result

    return timed


def wait_new_block(ethereum: Ethereum, current_block: int) -> Block:
    start_time = time.time()
    while True:
        latest_block = ethereum.w3.eth.getBlock("latest")
        if latest_block["number"] > current_block:
            print(
                f"Block Number: {latest_block['number']} (%s seconds)"
                % (time.time() - start_time)
            )
            return Block(
                number=latest_block["number"], timestamp=latest_block["timestamp"]
            )
        time.sleep(0.5)


def init_all_exchange_contracts(
    ethereum: Ethereum, pools: List[Pool], config: Config
) -> Dict[str, ExchangeInterface]:
    exchange_by_pool_address = {}
    for pool in pools:
        contract = ethereum.init_contract(pool)
        exchange = ExchangeFactory.create(contract, pool.type, debug=config.debug)
        exchange_by_pool_address[pool.address] = exchange
    return exchange_by_pool_address
