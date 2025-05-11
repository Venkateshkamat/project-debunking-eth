from web3 import Web3

# Connect to Sepolia public RPC
w3 = Web3(Web3.HTTPProvider("https://ethereum-sepolia.publicnode.com"))

# Define addresses
address1 = "0x6CA38c708c1F82eAED6520bEA36a224411297cda"
address2 = "0xb91545c1A71c4E55c11a9ee71f6AD0c65AD809e4"

balance1_wei = w3.eth.get_balance(address1)
balance2_wei = w3.eth.get_balance(address2)

balance1_eth = w3.from_wei(balance1_wei, 'ether')
balance2_eth = w3.from_wei(balance2_wei, 'ether')

print(f"Account 1 ({address1}) balance: {balance1_eth} ETH")
print(f"Account 2 ({address2}) balance: {balance2_eth} ETH")

