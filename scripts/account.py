from web3 import Web3
from eth_account import Account

# Generate accounts
acct1 = Account.create()
acct2 = Account.create()

print("Sender Address:", acct1.address)
print("Sender Private Key:", acct1.key.hex())

print("Receiver Address:", acct2.address)
print("Receiver Private Key:", acct2.key.hex())


# Sender Address: 0x6CA38c708c1F82eAED6520bEA36a224411297cda
# Sender Private Key: eaa3c90bd0f998caaa970032da17758a9cf41d47fadec2203b3927e3331ae50b  
# Receiver Address: 0x33fBE4350d1D6C00A81d7269B990Ea3cB9d5bEb7
# Receiver Private Key: fcde3dfd818153b18368c2d297022dd0c61626a79afa2ed1851596a2b3b00796