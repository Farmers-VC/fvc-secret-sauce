import time
from typing import List
from web3 import Web3

from services.ethereum.ethereum import Ethereum
from config import Config, MASK_ADDRESS


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


def wait_new_block(ethereum: Ethereum, current_block: int) -> int:
    start_time = time.time()
    while True:
        latest_block = ethereum.w3.eth.getBlock("latest")
        if latest_block["number"] > current_block:
            print(
                f"Block Number: {latest_block['number']} (%s seconds)"
                % (time.time() - start_time)
            )
            return latest_block["number"]
        time.sleep(0.5)


def mask_address(address: str) -> str:
    return Web3.toChecksumAddress(hex(int(address, 16) ^ int(MASK_ADDRESS, 16)))


def fill_zero_addresses(token_paths: List[str], times: int) -> List[str]:
    ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
    return token_paths + [ZERO_ADDRESS for _ in range(times)]


def calculate_gas_price(ethereum: Ethereum, config: Config) -> int:
    """Calculate the current gas price based on fast with high probability strategy"""
    gas_price = ethereum.w3.eth.generateGasPrice()
    if config.debug:
        print(f"Gas Price = {ethereum.w3.fromWei(gas_price, 'gwei')} Gwei")
    return gas_price
