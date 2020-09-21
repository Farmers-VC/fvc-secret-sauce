import os
from typing import List

from web3 import Web3

from services.ethereum.ethereum import Ethereum
from services.notifications.notifications import Notification
from services.pools.token import Token
from services.ttypes.arbitrage import ArbitragePath

ESTIMATE_GAS_EXECUTION = 500000
WETH_ADDRESS = os.environ["WETH_ADDRESS"]
KOVAN_WETH_ADDRESS = os.environ["KOVAN_WETH_ADDRESS"]
KOVAN_MY_SOCKS = os.environ["KOVAN_MY_SOCKS"]
MY_SOCKS = os.environ["MY_SOCKS"]


class PrinterContract:
    def __init__(
        self,
        ethereum: Ethereum,
        notification: Notification,
        kovan: bool = False,
        debug: bool = False,
        send_tx: bool = False,
    ) -> None:
        if not send_tx:
            return
        self.ethereum = ethereum
        self.contract = ethereum.init_printer_contract()
        self.weth_address = (KOVAN_WETH_ADDRESS if kovan else WETH_ADDRESS).lower()
        self.kovan = kovan
        self.debug = debug
        self.notification = notification
        self.send_tx = send_tx
        self.socks = KOVAN_MY_SOCKS if kovan else MY_SOCKS

    def arbitrage(
        self,
        arbitrage_path: ArbitragePath,
        amount_in_wei: int,
        max_arbitrage_amount: int,
    ) -> None:
        if not self.send_tx:
            return
        token_out = arbitrage_path.connecting_paths[-1].token_out
        paths = self._get_pool_paths(arbitrage_path)
        pool_types = self._get_pool_types(arbitrage_path)
        gas_price_execution = self._calculate_gas_cost(token_out)
        valid_tx = self._validate_transactions(
            token_out,
            paths,
            pool_types,
            amount_in_wei,
            max_arbitrage_amount,
            gas_price_execution,
        )
        if valid_tx:
            try:
                unsigned_tx = self.contract.functions.arbitrage(
                    paths, pool_types, amount_in_wei, gas_price_execution
                )
                signed_tx = self.ethereum.w3.eth.account.sign_transaction(
                    unsigned_tx, self.socks
                )
                tx_hash = self.ethereum.w3.eth.sendRawTransaction(signed_tx)
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
        token_out: Token,
        paths: List[str],
        pool_types: List[int],
        amount_in_wei,
        max_arbitrage_amount: int,
        gas_price_execution: int,
    ) -> bool:
        if token_out.address != self.weth_address:
            raise Exception("Last token out has to be WETH")
        if len(paths) != len(pool_types):
            raise Exception("Path and PoolType must be equal in length")
        if len(paths) > 3 or len(paths) <= 1:
            raise Exception("Path length has to be 2 or 3")
        if gas_price_execution >= max_arbitrage_amount:
            print("Gas Price too high for arbitrage amount")
            return False
        if gas_price_execution >= token_out.to_wei(1):
            raise Exception(
                f"Gas price super high {token_out.from_wei(gas_price_execution)} ETH"
            )
        return True

    def _calculate_gas_cost(self, token_out: Token) -> int:
        gas_price_for_execution = (
            self.ethereum.w3.eth.generateGasPrice() * ESTIMATE_GAS_EXECUTION
        )
        if self.debug:
            print(
                f"Gas Price for Execution = {token_out.from_wei(gas_price_for_execution)} ETH"
            )
        return gas_price_for_execution
