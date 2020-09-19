from dataclasses import dataclass
from typing import List

from services.pools.pool import Pool
from services.pools.token import Token


@dataclass
class ConnectingPath:
    pool: Pool
    token_in: Token
    token_out: Token


@dataclass
class ArbitragePath:
    connecting_paths: List[ConnectingPath]
