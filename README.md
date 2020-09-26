# fvc-secret-sauce

Usage: main.py [OPTIONS]
```
Options:
  --kovan         Point to Kovan test network
  --debug         Display logs
  --send-tx       Send arbitrage transactions on-chain
  --max-amount FLOAT  Set max amount to trade with in WETH
  --min-amount FLOAT  Set min amount to trade with in WETH
  --help          Show this message and exit.
```

# Installation

1. virtualenv venv
2. source venv/bin/activate
3. pip install -r requirements.txt

# Environment
Requirement: install direnv: https://direnv.net/docs/installation.html
1. cp .envrc.default .envrc
2. direnv allow
