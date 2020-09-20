from typing import List

from web3 import Web3

from services.ethereum.ethereum import Ethereum
from services.notifications.notifications import Notification
from services.ttypes.arbitrage import ArbitragePath

ESTIMATE_GAS_EXECUTION = 800000


class PrinterContract:
    def __init__(
        self,
        ethereum: Ethereum,
        notification: Notification,
        kovan: bool = False,
        debug: bool = False,
    ) -> None:
        self.ethereum = ethereum
        self.contract = ethereum.init_printer_contract()
        self.weth_address = (
            "0xa0f764e120459bca39db7e57a0ce975a489ab4fa"
            if kovan
            else "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
        ).lower()
        self.kovan = kovan
        self.debug = debug
        self.notification = notification

    def arbitrage(
        self,
        arbitrage_path: ArbitragePath,
        amount_in_wei: int,
        min_amount_out_wei: int,
    ) -> None:
        paths = self._get_pool_paths(arbitrage_path)
        pool_types = self._get_pool_types(arbitrage_path)
        valid_tx = self._validate_transactions(
            arbitrage_path, paths, pool_types, amount_in_wei, min_amount_out_wei
        )
        if valid_tx:
            try:
                tx_hash = self.contract.functions.arbitrage(
                    paths, pool_types, amount_in_wei, min_amount_out_wei
                ).transact()
                self.notification.send_all_message(
                    f"Printing Money $$$$ - tx_hash: {tx_hash}"
                )
            except Exception as e:
                self.notification.send_slack(f"{str(e)}")

    def _get_pool_paths(self, arbitrage_path: ArbitragePath) -> List[str]:
        return [
            Web3.toChecksumAddress(path.pool.address)
            for path in arbitrage_path.connecting_paths
        ]

    def _get_pool_types(self, arbitrage_path: ArbitragePath) -> List[int]:
        return [path.pool.type.value for path in arbitrage_path.connecting_paths]

    def _validate_transactions(
        self,
        arbitrage_path: ArbitragePath,
        paths: List[str],
        pool_types: List[int],
        amount_in_wei,
        min_amount_out_wei,
    ) -> bool:
        token_out = arbitrage_path.connecting_paths[-1].token_out
        if token_out.address != self.weth_address:
            raise Exception("Last token out has to be WETH")
        if len(paths) != len(pool_types):
            raise Exception("Path and PoolType must be equal in length")
        if len(paths) > 3 or len(paths) <= 1:
            raise Exception("Path length has to be 2 or 3")
        if amount_in_wei >= min_amount_out_wei:
            raise Exception("Amount out is lower than Amount in")
        min_arbitrage_amount = min_amount_out_wei - amount_in_wei
        gas_price_for_execution = (
            self.ethereum.w3.eth.generateGasPrice() * ESTIMATE_GAS_EXECUTION
        )
        if self.debug:
            print(
                f"Gas Price for Execution = {token_out.from_wei(gas_price_for_execution)} ETH"
            )
        if gas_price_for_execution >= min_arbitrage_amount:
            print("Gas Price too high for arbitrage amount")
            return False
        if gas_price_for_execution >= token_out.to_wei(1):
            raise Exception(
                f"Gas price super high {token_out.from_wei(gas_price_for_execution)} ETH"
            )
        return True
