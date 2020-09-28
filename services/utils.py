import time

from services.ethereum.ethereum import Ethereum
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
