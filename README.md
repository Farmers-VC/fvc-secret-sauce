# fvc-secret-sauce

Usage: main.py [OPTIONS]
```
Options:
  --kovan         Point to Kovan test network
  --debug         Display logs
  --send-tx       Send arbitrage transactions on-chain
  --amount FLOAT  Set max amount to trade with in WETH
  --help          Show this message and exit.
```

# Installation

virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Environment
cp .envrc.default .envrc
direnv allow
