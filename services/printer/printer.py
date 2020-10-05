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

    def arbitrage_on_chain(
        self,
        arbitrage_path: ArbitragePath,
        latest_block: int,
        tx_hash: str = "",
        send_tx: bool = False,
        consecutive_arbs: int = None,
    ) -> bool:
        """Return True if arbitrage is/would have been successful on-chain, False otherwise"""
        if self._safety_send(arbitrage_path) and self._validate_transactions(
            arbitrage_path
        ):
            self._display_arbitrage(
                arbitrage_path, latest_block, tx_hash, consecutive_arbs
            )
            if send_tx:
                return self._send_transaction_on_chain(arbitrage_path)
            return True
        else:
            print(
                stylize(
                    f"Estimate Gas Failed {arbitrage_path.print(latest_block, tx_hash, consecutive_arbs)}",
                    fg("light_red"),
                )
            )
            return False

    def _safety_send(self, arbitrage_path: ArbitragePath) -> bool:
        """This function will simulate sending the transaction on-chain and let us know if it would go through"""
        try:
            # Run estimateGas to see if the transaction would go through
            self.contract.functions.arbitrage(
                arbitrage_path.token_paths,
                arbitrage_path.all_min_amount_out_wei_grouped,
                arbitrage_path.optimal_amount_in_wei,
                arbitrage_path.gas_price_execution,
                arbitrage_path.pool_types,
                arbitrage_path.max_block_height,
            ).estimateGas({"from": self.executor_address})
            return True
        except Exception as e:
            print(f"This transaction would not go through: {str(e)}")
            return False

    def _send_transaction_on_chain(self, arbitrage_path: ArbitragePath) -> bool:
        """Trigger the arbitrage transaction on-chain"""
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
                return True
            else:
                self.notification.send_slack_printing_tx(tx_hash_url, success=False)
        except TimeExhausted as e:
            self.notification.send_slack_errors(
                f"Transaction failed {tx_hash_url}: {str(e)}"
            )
        except Exception as e:
            self.notification.send_slack_errors(f"Exception: {str(e)}")
        return False

    def _building_tx_and_signing_and_send(
        self,
        arbitrage_path: ArbitragePath,
    ) -> str:
        """Helper function to build the transaction and signed it with priv key"""
        unsigned_tx = self.contract.functions.arbitrage(
            arbitrage_path.token_paths,
            arbitrage_path.all_min_amount_out_wei_grouped,
            arbitrage_path.optimal_amount_in_wei,
            arbitrage_path.gas_price_execution,
            arbitrage_path.pool_types,
            arbitrage_path.max_block_height,
        ).buildTransaction(
            {
                "chainId": 42 if self.config.kovan else 1,
                "gas": self.config.get_int("ESTIMATE_GAS_LIMIT"),
                "gasPrice": int(arbitrage_path.gas_price),
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
        if token_out.address != self.weth_address:
            self.notification.send_slack_errors("Last token out has to be WETH")
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
        latest_block: int,
        tx_hash: str = "",
        consecutive_arbs: int = None,
    ) -> None:
        if self.config.strategy != "fresh" or consecutive_arbs >= 2:
            to_print = arbitrage_path.print(latest_block, tx_hash, consecutive_arbs)
            if self.config.strategy == "snipe":
                self.notification.send_snipe_noobs(to_print)
            else:
                self.notification.send_slack_arbitrage(to_print)
