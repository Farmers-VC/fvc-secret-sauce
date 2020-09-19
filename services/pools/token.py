class Token:
    def __init__(self, name: str, address: str, decimal: int) -> None:
        self.name = name
        self.address = address.lower()
        self.decimal = decimal

    def to_wei(self, amount: float) -> int:
        return int(amount * (10 ** self.decimal))

    def from_wei(self, amount_in_wei: int) -> float:
        return amount_in_wei / (10 ** self.decimal)
