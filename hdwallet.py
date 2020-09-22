# https://github.com/trezor/python-mnemonic
from mnemonic import Mnemonic

mnemo = Mnemonic("english")
words = mnemo.generate(strength=256)

print("Mnemonic Phrase:\n")
print(words)

# seed = mnemo.to_seed(words, passphrase="")
