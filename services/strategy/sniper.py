from config import Config
from services.ethereum.ethereum import Ethereum
from services.ttypes.arbitrage import ArbitragePath


class Sniper:
    def __init__(self, ethereum: Ethereum, config: Config) -> None:
        self.ethereum = ethereum
        self.config = config

    def scan_mempool_and_snipe(self, arbitrage_path: ArbitragePath):
        """Watch the mempool for an arbitrageur targetting `arbitrage_path`
        Once detected, we snipe them by submitting a transaction with a higher gas price.
        """
        self._scan_mempool(arbitrage_path)

    def _scan_mempool(self, arbitrage_path):
        pending_tx = self.ethereum.w3.geth.txpool.content()["pending"]
        breakpoint()
