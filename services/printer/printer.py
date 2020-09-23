from typing import List

from colored import fg, stylize
from web3 import Web3
from web3.exceptions import TimeExhausted

from config import Config
from services.ethereum.ethereum import Ethereum
from services.notifications.notifications import Notification
from services.pools.token import Token
from services.ttypes.arbitrage import ArbitragePath
from services.ttypes.contract import ContractTypeEnum

MAX_LEGS_PER_TRADE = 4
BURN_ADDRESS = "0x0000000000000000000000000000000000000000"


class PrinterContract:
    def __init__(
        self, ethereum: Ethereum, notification: Notification, config: Config
    ) -> None:
        self.ethereum = ethereum
        self.contract = ethereum.init_printer_contract()
        self.config = config
        self.weth_address = self.config.get("WETH_ADDRESS").lower()
        self.notification = notification
        self.socks = self.config.get("MY_SOCKS")
        self.executor_address = self.config.get("EXECUTOR_ADDRESS")

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
        gas_price_execution = gas_price * self.config.get_int("ESTIMATE_GAS_EXECUTION")
        current_block_height = self.ethereum.w3.eth.blockNumber
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
                current_block_height + (5 if self.config.kovan else 1),
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
        if self.config.send_tx:
            try:
                # Run estimateGas to see if the transaction would go through
                self.contract.functions.arbitrage(
                    paths, pool_types, amount_in_wei, gas_price_execution
                ).estimateGas({"from": self.executor_address})
            except Exception as e:
                self.notification.send_slack_errors(f"Gas Estimation Failed: {str(e)}")
                return

            try:
                tx_hash = self._building_tx_and_signing_and_send(
                    paths, pool_types, amount_in_wei, gas_price_execution, gas_price
                )
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
        paths: List[str],
        pool_types: List[int],
        amount_in_wei: int,
        gas_price_execution: int,
        gas_price: int,
    ) -> str:
        """Helper function to build the transaction and signed it with priv key"""
        unsigned_tx = self.contract.functions.arbitrage(
            paths, pool_types, amount_in_wei, gas_price_execution
        ).buildTransaction(
            {
                "chainId": 42 if self.config.kovan else 1,
                "gas": self.config.get_int("ESTIMATE_GAS_EXECUTION"),
                "gasPrice": int(gas_price * 1.5),
                "nonce": self.ethereum.w3.eth.getTransactionCount(
                    self.executor_address
                ),
            }
        )
        signed_tx = self.ethereum.w3.eth.account.sign_transaction(
            unsigned_tx, self.socks
        )
        tx_hash = self.ethereum.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        print(
            stylize(
                f"Sending transaction {tx_hash.hex()} ...",
                fg("yellow"),
            )
        )
        return tx_hash.hex()

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
        if gas_price_execution >= token_out.to_wei(max_arbitrage_amount):
            self.notification.send_slack_errors(
                "Gas Price too high for arbitrage amount"
            )
            return False
        if gas_price_execution >= token_out.to_wei(1):
            self.notification.send_slack_errors(
                f"Gas price super high {token_out.from_wei(gas_price_execution)} ETH"
            )
            return False
        return True

    def _calculate_gas_price(self) -> int:
        """Calculate the current gas price based on fast with high probability strategy"""
        gas_price = self.ethereum.w3.eth.generateGasPrice()
        if self.config.debug:
            print(f"Gas Price = {self.ethereum.w3.fromWei(gas_price, 'gwei')} Gwei")
        return gas_price

    def _display_emoji_by_amount(self, max_arbitrage_amount: int, emoji: str) -> str:
        times = 1
        if max_arbitrage_amount > 0.5 and max_arbitrage_amount < 1.0:
            times = 2
        if max_arbitrage_amount >= 1.0 and max_arbitrage_amount < 1.5:
            times = 4
        if max_arbitrage_amount >= 1.5 and max_arbitrage_amount < 2.0:
            times = 6
        if max_arbitrage_amount >= 2.0:
            times = 8
        return "".join([emoji for _ in range(times)])

    def _display_arbitrage(
        self,
        arbitrage_path: ArbitragePath,
        token_out: Token,
        optimal_amount_in: int,
        max_arbitrage_amount: int,
        gas_price: int,
        gas_price_execution: int,
        max_block_height: int,
    ) -> None:
        paths = f"{arbitrage_path.connecting_paths[0].token_in.name} ({arbitrage_path.connecting_paths[0].pool.type.name})"
        for path in arbitrage_path.connecting_paths:
            paths += f" -> {path.token_out.name} ({path.pool.type.name})"
        beers = self._display_emoji_by_amount(max_arbitrage_amount, ":beer:")
        arbitrage_result = f"{beers}\nOpportunity: *{max_arbitrage_amount}* ETH :moneybag:\nPath: {paths} \nAmount in: {token_out.from_wei(optimal_amount_in)} ETH\nGas Price: {self.ethereum.w3.fromWei(gas_price, 'gwei')} Gwei"
        contract_path_input = []
        contract_type_input = []
        min_amount_outs_input = []
        for index in range(MAX_LEGS_PER_TRADE):
            try:
                pool_address = arbitrage_path.connecting_paths[index].pool.address
                contract_type = arbitrage_path.connecting_paths[index].pool.type.value
                min_amount_out = 0  # TODO: Calculate min amount out per leg
            except Exception:
                pool_address = BURN_ADDRESS
                contract_type = ContractTypeEnum.NONE.value
                min_amount_out = 0

            contract_path_input.append(pool_address)
            contract_type_input.append(str(contract_type))
            min_amount_outs_input.append(min_amount_out)

        contract_input = f'{contract_path_input},{contract_type_input},{min_amount_outs_input},"{optimal_amount_in}","{gas_price_execution}", "{max_block_height}"'.replace(
            "'", '"'
        )
        slack_message = arbitrage_result + (
            f"\n{contract_input}\n------------------------------------------"
        )
        self.notification.send_slack_arbitrage(slack_message)
        if max_arbitrage_amount > 1:
            self.notification.send_twilio(arbitrage_result)
