from web3 import Web3
from eth_account import Account

# Good faucet - https://sepolia-faucet.pk910.de/

# Transactions are found at https://sepolia.etherscan.io/

# Setup
w3 = Web3(Web3.HTTPProvider("https://ethereum-sepolia.publicnode.com"))

sender_address = "0x6CA38c708c1F82eAED6520bEA36a224411297cda"
receiver_address = "0xb91545c1A71c4E55c11a9ee71f6AD0c65AD809e4"
private_key = "eaa3c90bd0f998caaa970032da17758a9cf41d47fadec2203b3927e3331ae50b"

# Set gas price
gas_price = w3.to_wei(100, 'gwei')  # 100 gwei is safe for Sepolia

nonce = w3.eth.get_transaction_count(sender_address, 'pending')
# Build transaction
tx = {
    'nonce': nonce,
    'to': receiver_address,
    'value': w3.to_wei(0.01, 'ether'),
    'gas': 21000,
    'gasPrice': gas_price,
    'chainId': 11155111  # Sepolia chain ID
}

# Sign & send
signed_tx = w3.eth.account.sign_transaction(tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

print("✅ Transaction sent!") # 0.01 ETH (sent) + 0.0021 ETH (fee) = 0.0121 ETH
print("🔗 TX Hash:", tx_hash.hex())