import os
import os.path

THIS_DIR = os.path.abspath(os.path.dirname(__file__))

# Etherscan
ETHERSCAN_API_KEY = os.environ["ETHERSCAN_API_KEY"]
ETHERSCAN_API = "https://api.etherscan.io/api"

# Ethereum
ETHEREUM_WS_URI = os.environ["ETHEREUM_WS_URI"]
ETHEREUM_HTTP_URI = os.environ["ETHEREUM_HTTP_URI"]
EXECUTOR_ADDRESS = os.environ["EXECUTOR_ADDRESS"]
MY_SOCKS = os.environ["MY_SOCKS"]
WETH_ADDRESS = os.environ["WETH_ADDRESS"]
PRINTER_ADDRESS = os.environ["PRINTER_ADDRESS"]

# Arbitrage
MAX_STEP_SUPPORTED = 3
ESTIMATE_GAS_EXECUTION = 500000
ESTIMATE_GAS_LIMIT = 1000000
INCREMENTAL_STEP = 0.1

# Path
TOKEN_BLACKLIST_YAML_PATH = os.path.join(THIS_DIR, "pools/blacklist.yaml")
TOKEN_YAML_PATH = os.path.join(THIS_DIR, "pools/tokens.yaml")
POOL_YAML_PATH = os.path.join(THIS_DIR, "pools/pools.yaml")
ABI_PATH = os.path.join(THIS_DIR, "services/ethereum/abi")
SNIPING_NOOBS_YAML_PATH = os.path.join(THIS_DIR, "services/strategy/noobs.yaml")

# Twilio
AGENT_PHONE_NUMBERS = os.environ.get("AGENT_PHONE_NUMBERS")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")

# Slack
SLACK_ERRORS_WEBHOOK = os.environ["SLACK_ERRORS_WEBHOOK"]
SLACK_PRINTING_TX_WEBHOOK = os.environ["SLACK_PRINTING_TX_WEBHOOK"]
SLACK_ARBITRAGE_OPPORTUNITIES_WEBHOOK = os.environ[
    "SLACK_ARBITRAGE_OPPORTUNITIES_WEBHOOK"
]
SLACK_SNIPE_WEBHOOK = os.environ["SLACK_SNIPE_WEBHOOK"]

# Kovan Env
KOVAN_ETHEREUM_WS_URI = os.environ["KOVAN_ETHEREUM_WS_URI"]
KOVAN_ETHEREUM_HTTP_URI = os.environ["KOVAN_ETHEREUM_HTTP_URI"]
KOVAN_EXECUTOR_ADDRESS = os.environ["KOVAN_EXECUTOR_ADDRESS"]
KOVAN_MY_SOCKS = os.environ["KOVAN_MY_SOCKS"]
KOVAN_POOL_YAML_PATH = os.path.join(THIS_DIR, "pools/kovan/pools.yaml")
KOVAN_PRINTER_ADDRESS = os.environ["KOVAN_PRINTER_ADDRESS"]
KOVAN_SLACK_WEBHOOK_URI = os.environ.get("KOVAN_SLACK_WEBHOOK_URI")
KOVAN_TOKEN_BLACKLIST_YAML_PATH = os.path.join(THIS_DIR, "pools/blacklist.yaml")
KOVAN_TOKEN_YAML_PATH = os.path.join(THIS_DIR, "pools/kovan/tokens.yaml")
KOVAN_WETH_ADDRESS = os.environ["KOVAN_WETH_ADDRESS"]
KOVAN_INCREMENTAL_STEP = 1.0
KOVAN_SLACK_ERRORS_WEBHOOK = os.environ["KOVAN_SLACK_ERRORS_WEBHOOK"]
KOVAN_SLACK_PRINTING_TX_WEBHOOK = os.environ["KOVAN_SLACK_PRINTING_TX_WEBHOOK"]
KOVAN_SLACK_ARBITRAGE_OPPORTUNITIES_WEBHOOK = os.environ[
    "KOVAN_SLACK_ARBITRAGE_OPPORTUNITIES_WEBHOOK"
]


class Config:
    def __init__(
        self,
        kovan: bool = False,
        debug: bool = False,
        send_tx: bool = False,
        max_amount: float = 6.0,
        min_amount: float = 3.0,
        is_snipe: bool = False,
    ):
        self.kovan = kovan
        self.debug = debug
        self.send_tx = send_tx
        self.max_amount = max_amount
        self.min_amount = min_amount
        self.is_snipe = is_snipe

    def get(self, name: str):
        if self.kovan:
            try:
                result = eval(f"KOVAN_{name}")
            except NameError:
                result = eval(name)
        else:
            result = eval(name)
        return result

    def get_int(self, name: str):
        result = self.get(name)
        return int(result)

    def get_float(self, name: str):
        result = self.get(name)
        return float(result)
