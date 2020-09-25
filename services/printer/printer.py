from colored import fg, stylize
from web3.exceptions import TimeExhausted

from config import Config
from services.ethereum.ethereum import Ethereum
from services.notifications.notifications import Notification
from services.ttypes.arbitrage import ArbitragePath


class PrinterContract:
    def __init__(
        self, ethereum: Ethereum, notification: Notification, config: Config
    ) -> None:
        self.ethereum = ethereum
        self.contract = ethereum.init_printer_contract()
        self.config = config
        self.weth_address = self.config.get("WETH_ADDRESS").lower()
        self.notification = notification
        self.executor_address = self.config.get("EXECUTOR_ADDRESS")

    def arbitrage(
        self,
        arbitrage_path: ArbitragePath,
    ) -> None:
        current_block = self.ethereum.w3.eth.blockNumber
        arbitrage_path.max_block_height = current_block + (
            15 if self.config.kovan else 2
        )
        valid_tx = self._validate_transactions(arbitrage_path)
        if valid_tx:
            self._display_arbitrage(
                arbitrage_path,
                current_block,
            )
            self._send_transaction_on_chain(arbitrage_path)

    def _send_transaction_on_chain(self, arbitrage_path: ArbitragePath) -> None:
        """Trigger the arbitrage transaction on-chain"""
        if self.config.send_tx:
            executor_balance = self.ethereum.w3.eth.getBalance(
                self.ethereum.w3.toChecksumAddress(self.executor_address)
            )
            if (
                executor_balance < 2000000000000000000
                or not arbitrage_path.contain_token(
                    "0xf0fac7104aac544e4a7ce1a55adf2b5a25c65bd1"
                )
            ):
                print(
                    f"Balance ({executor_balance}) under 2 ETH or does not contain PAMP"
                )
                return
            try:
                # Run estimateGas to see if the transaction would go through
                self.contract.functions.arbitrage(
                    arbitrage_path.pool_paths,
                    arbitrage_path.pool_types,
                    arbitrage_path.all_min_amount_out_wei,
                    arbitrage_path.optimal_amount_in_wei,
                    arbitrage_path.gas_price_execution,
                    arbitrage_path.max_block_height,
                ).estimateGas({"from": self.executor_address})
            except Exception as e:
                print(f"Gas Estimation Failed: {str(e)}")
                return

            try:
                tx_hash = self._building_tx_and_signing_and_send(arbitrage_path)
                receipt = self.ethereum.w3.eth.waitForTransactionReceipt(tx_hash)
                etherscan_url = (
                    "https://kovan.etherscan.io/"
                    if self.config.kovan
                    else "https://etherscan.io"
                )
                tx_hash_url = f"{etherscan_url}/tx/{tx_hash}"
                if receipt["status"] == 1:
                    self.notification.send_slack_printing_tx(tx_hash_url, success=True)
                    self.notification.send_twilio(f"Brrrrrr: {tx_hash_url}")
                else:
                    self.notification.send_slack_printing_tx(tx_hash_url, success=False)
            except TimeExhausted as e:
                self.notification.send_slack_errors(
                    f"Transaction failed {tx_hash_url}: {str(e)}"
                )
            except Exception as e:
                self.notification.send_slack_errors(f"Exception: {str(e)}")

    def _building_tx_and_signing_and_send(
        self,
        arbitrage_path: ArbitragePath,
    ) -> str:
        """Helper function to build the transaction and signed it with priv key"""
        unsigned_tx = self.contract.functions.arbitrage(
            arbitrage_path.pool_paths,
            arbitrage_path.pool_types,
            arbitrage_path.all_min_amount_out_wei,
            arbitrage_path.optimal_amount_in_wei,
            arbitrage_path.gas_price_execution,
            arbitrage_path.max_block_height,
        ).buildTransaction(
            {
                "chainId": 42 if self.config.kovan else 1,
                "gas": self.config.get_int("ESTIMATE_GAS_LIMIT"),
                "gasPrice": int(arbitrage_path.gas_price * 1.1),
                "nonce": self.ethereum.w3.eth.getTransactionCount(
                    self.executor_address
                ),
            }
        )
        signed_tx = self.ethereum.w3.eth.account.sign_transaction(
            unsigned_tx, self.config.get("MY_SOCKS")
        )
        tx_hash = self.ethereum.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        print(
            stylize(
                f"Sending transaction {tx_hash.hex()} ...",
                fg("yellow"),
            )
        )
        return tx_hash.hex()

    def _validate_transactions(
        self,
        arbitrage_path: ArbitragePath,
    ) -> bool:
        token_out = arbitrage_path.token_out
        paths = arbitrage_path.pool_paths
        pool_types = arbitrage_path.pool_types
        if token_out.address != self.weth_address:
            self.notification.send_slack_errors("Last token out has to be WETH")
            return False
        if len(paths) != len(pool_types):
            self.notification.send_slack_errors(
                "Path and PoolType must be equal in length"
            )
            return False
        if len(paths) > 3 or len(paths) <= 1:
            self.notification.send_slack_errors("Path length has to be 2 or 3")
            return False
        if (
            arbitrage_path.gas_price_execution
            >= arbitrage_path.max_arbitrage_amount_wei
        ):
            self.notification.send_slack_errors(
                "Gas Price too high for arbitrage amount"
            )
            return False
        if arbitrage_path.gas_price_execution >= token_out.to_wei(1):
            self.notification.send_slack_errors(
                f"Gas price super high {token_out.from_wei(arbitrage_path.gas_price_execution)} ETH"
            )
            return False
        return True

    def _display_arbitrage(
        self,
        arbitrage_path: ArbitragePath,
        current_block: int,
    ) -> None:
        to_print = arbitrage_path.print(current_block)
        self.notification.send_slack_arbitrage(to_print)
