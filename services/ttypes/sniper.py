from dataclasses import dataclass
from typing import List

from services.pools.pool import Pool


@dataclass
class SnipingNoob:
    address: str


@dataclass
class SnipingArbitrage:
    pools: List[Pool]
    gas_price: int
