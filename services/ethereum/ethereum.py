import json
import os.path

# import requests
from web3 import Web3
from web3.eth import Contract

from services.pools.pool import Pool
from services.ttypes.contract import ContractTypeEnum

# import os
THIS_DIR = os.path.abspath(os.path.dirname(__file__))

# API_KEY = os.environ['ETHERSCAN_API_KEY']
# ETHERSCAN_API = "https://api.etherscan.io/api"


class Ethereum:
    def __init__(self, w3: Web3) -> None:
        self.w3 = w3

    def init_contract(self, pool: Pool) -> Contract:
        """From an address, initialize a web3.eth.Contract object
        """
        # url = f"{ETHERSCAN_API}?module=contract&action=getabi&address={address}&apikey={API_KEY}"
        # resp = requests.get(url)
        # json_resp = json.loads(resp.text)
        # contract_abi = json_resp['result']
        # breakpoint()
        contract_abi = self._get_abi_by_contract_type(pool.type)
        my_contract = self.w3.eth.contract(address=Web3.toChecksumAddress(pool.address), abi=contract_abi)
        return my_contract

    def _get_abi_by_contract_type(self, contract_type: ContractTypeEnum) -> str:
        if contract_type == ContractTypeEnum.BPOOL:
            json_file = 'bpool_abi.json'
        if contract_type == ContractTypeEnum.UNISWAP:
            json_file = 'uniswap_pair_abi.json'
        with open(os.path.join(THIS_DIR, f'abi/{json_file}')) as f:
            contract_abi = json.load(f)
            return contract_abi
