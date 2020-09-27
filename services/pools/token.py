from web3 import Web3


class Token:
    def __init__(self, name: str, address: str, decimal: int) -> None:
        self.name = name
        self.address = address.lower()
        self.decimal = decimal
        self.checksum_address = Web3.toChecksumAddress(self.address)

    def to_wei(self, amount: float) -> int:
        return int(amount * (10 ** self.decimal))

    def from_wei(self, amount_in_wei: int) -> float:
        return amount_in_wei / (10 ** self.decimal)
