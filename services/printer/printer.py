import os
from typing import List

from colored import fg, stylize
from web3 import Web3
from web3.exceptions import TimeExhausted

from services.ethereum.ethereum import Ethereum
from services.notifications.notifications import Notification
from services.pools.token import Token
from services.ttypes.arbitrage import ArbitragePath

ESTIMATE_GAS_EXECUTION = 600000
EXECUTOR_ADDRESS = os.environ["EXECUTOR_ADDRESS"]
MY_SOCKS = os.environ["MY_SOCKS"]
WETH_ADDRESS = os.environ["WETH_ADDRESS"]

KOVAN_EXECUTOR_ADDRESS = os.environ["KOVAN_EXECUTOR_ADDRESS"]
KOVAN_MY_SOCKS = os.environ["KOVAN_MY_SOCKS"]
KOVAN_WETH_ADDRESS = os.environ["KOVAN_WETH_ADDRESS"]


class PrinterContract:
    def __init__(
        self,
        ethereum: Ethereum,
        notification: Notification,
        kovan: bool = False,
        debug: bool = False,
        send_tx: bool = False,
    ) -> None:
        self.ethereum = ethereum
        self.contract = ethereum.init_printer_contract()
        self.weth_address = (KOVAN_WETH_ADDRESS if kovan else WETH_ADDRESS).lower()
        self.kovan = kovan
        self.debug = debug
        self.notification = notification
        self.send_tx = send_tx
        self.socks = KOVAN_MY_SOCKS if kovan else MY_SOCKS
        self.executor_address = KOVAN_EXECUTOR_ADDRESS if kovan else EXECUTOR_ADDRESS

    def arbitrage(
        self,
        arbitrage_path: ArbitragePath,
        amount_in_wei: int,
        max_arbitrage_amount: int,
    ) -> None:
        token_out = arbitrage_path.connecting_paths[-1].token_out
        paths = self._get_pool_paths(arbitrage_path)
        pool_types = self._get_pool_types(arbitrage_path)
        gas_price = self._calculate_gas_price()
        gas_price_execution = gas_price * ESTIMATE_GAS_EXECUTION
        valid_tx = self._validate_transactions(
            token_out,
            paths,
            pool_types,
            amount_in_wei,
            max_arbitrage_amount,
            gas_price_execution,
        )
        if valid_tx:
            self._display_arbitrage(
                arbitrage_path,
                token_out,
                amount_in_wei,
                max_arbitrage_amount,
                gas_price,
                gas_price_execution,
            )
            self._send_transaction_on_chain(
                paths, pool_types, amount_in_wei, gas_price_execution, gas_price
            )

    def _send_transaction_on_chain(
        self,
        paths: List[str],
        pool_types: List[int],
        amount_in_wei: int,
        gas_price_execution: int,
        gas_price: int,
    ) -> None:
        """Trigger the arbitrage transaction on-chain"""
        if self.send_tx and input("Print Money? (y/n) ") == "y":
            try:
                unsigned_tx = self.contract.functions.arbitrage(
                    paths, pool_types, amount_in_wei, gas_price_execution
                ).buildTransaction(
                    {
                        "chainId": 42 if self.kovan else 1,
                        "gas": ESTIMATE_GAS_EXECUTION,
                        "gasPrice": gas_price,
                        "nonce": self.ethereum.w3.eth.getTransactionCount(
                            self.executor_address
                        ),
                    }
                )
                signed_tx = self.ethereum.w3.eth.account.sign_transaction(
                    unsigned_tx, self.socks
                )
                tx_hash = self.ethereum.w3.eth.sendRawTransaction(
                    signed_tx.rawTransaction
                )

                print(
                    stylize(
                        f"Sending transaction {tx_hash.hex()} ...",
                        fg("yellow"),
                    )
                )
                self.ethereum.w3.eth.waitForTransactionReceipt(tx_hash.hex())
                print(
                    stylize(
                        f"Transaction executed!!!!",
                        fg("green"),
                    )
                )
                self.notification.send_slack(
                    f"Printing Money $$$$ - tx_hash: {tx_hash.hex()}"
                )
            except TimeExhausted as e:
                self.notifications.send_slack(
                    f"Transaction failed {tx_hash.hex()}: {str(e)}"
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
        if gas_price_execution >= token_out.to_wei(max_arbitrage_amount):
            print("Gas Price too high for arbitrage amount")
            return False
        if gas_price_execution >= token_out.to_wei(1):
            raise Exception(
                f"Gas price super high {token_out.from_wei(gas_price_execution)} ETH"
            )
        return True

    def _calculate_gas_price(self) -> int:
        """Calculate the current gas price based on fast with high probability strategy"""
        gas_price = self.ethereum.w3.eth.generateGasPrice()
        if self.debug:
            print(f"Gas Price = {self.ethereum.w3.fromWei(gas_price, 'gwei')} Gwei")
        return gas_price

    def _display_arbitrage(
        self,
        arbitrage_path: ArbitragePath,
        token_out: Token,
        optimal_amount_in: int,
        max_arbitrage_amount: int,
        gas_price: int,
        gas_price_execution: int,
    ) -> None:
        paths = f"{arbitrage_path.connecting_paths[0].token_in.name} ({arbitrage_path.connecting_paths[0].pool.type.name})"
        for path in arbitrage_path.connecting_paths:
            paths += f" -> {path.token_out.name} ({path.pool.type.name})"
        arbitrage_result = f"Arbitrage: {paths} \nAmount: +{max_arbitrage_amount} ETH \nAmount in: {token_out.from_wei(optimal_amount_in)} ETH\nGas Price: {self.ethereum.w3.fromWei(gas_price, 'gwei')} Gwei"
        print(
            stylize(
                arbitrage_result,
                fg("light_blue"),
            )
        )

        contract_path_input = []
        contract_type_input = []
        for connecting_path in arbitrage_path.connecting_paths:
            contract_path_input.append(connecting_path.pool.address)
            contract_type_input.append(str(connecting_path.pool.type.value))
        contract_input = f'{contract_path_input},{contract_type_input},"{optimal_amount_in}","{gas_price_execution}"'.replace(
            "'", '"'
        )
        slack_message = arbitrage_result + (
            f"\n{contract_input}\n------------------------------------------"
        )
        self.notification.send_slack(slack_message)
        if max_arbitrage_amount > 0.5:
            self.notification.send_twilio(arbitrage_result)
