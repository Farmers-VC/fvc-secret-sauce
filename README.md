# fvc-secret-sauce

# Strategies
## Fresh Strategy
Scan **fresh pools** every 200 blocks for new arbitrage opportunities. 
Any arbitrage that last more than 2 consecutives blocks will be executed if the flag `--send-tx` is passed.
Play with different `--min-liquidity` and `--max-liquidity` to ensure processing all arbitrage paths under 10 seconds.
```
Usage: fresh.py [OPTIONS]

Options:
  --kovan                  point to kovan test network
  --debug                  Display logs
  --send-tx                Flag to activate sending tx on-chain
  --max-amount FLOAT       Set max amount to trade with in WETH (Default:
                           6.0)

  --min-amount FLOAT       set min amount to trade with in weth (default:
                           3.0)

  --min-liquidity INTEGER  Set minimum liquidity (Default: 30,000)
  --max-liquidity INTEGER  Set max liquidity (Default: 100,000)
  --help                   Show this message and exit.
```

## Snipe Strategy
Observe the mempool for arbitrageurs that we are **sniping**. 
A single arbitrategeur can be passed via `--address` or a list can be defined in yamls/snipers.yaml.
Goal is to observe any arbitrage and outbid them by 1 Wei.
```
Usage: snipe.py [OPTIONS]

Options:
  --kovan             Point to Kovan test network
  --debug             Display logs
  --max-amount FLOAT  Set max amount to trade with in WETH (Default: 6.0)
  --min-amount FLOAT  Set min Amount to trade with in WETH (Default: 3.0)
  --send-tx           Send the transaction on-chain
  --address TEXT      Specify a specific arbitrageur address to snipe
  --help              Show this message and exit.
```


## Scan Strategy
Simply scan pools for arbitrage opportunities.
```
Usage: scan.py [OPTIONS]

Options:
  --kovan                  Point to Kovan test network
  --debug                  Display logs
  --max-amount FLOAT       Set max amount to trade with in WETH (Default:
                           6.0)

  --min-amount FLOAT       Set min Amount to trade with in WETH (Default:
                           3.0)

  --min-liquidity INTEGER  Set minimum liquidity (Default: 30,000)
  --max-liquidity INTEGER  Set max liquidity (Default: 500,000)
  --help                   Show this message and exit.
```

# Installation

1. virtualenv venv
2. source venv/bin/activate
3. pip install -r requirements.txt

# Environment
Requirement: install direnv: https://direnv.net/docs/installation.html
1. cp .envrc.default .envrc
2. direnv allow
