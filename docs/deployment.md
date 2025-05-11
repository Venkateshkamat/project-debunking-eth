# Deploying & Testing an Ethereum Node

This document covers what you need to install and the primary snippets of code that are important to sending ETH. You can read about web3's full documentation [**here**](https://web3py.readthedocs.io/en/stable/)

There are also example files in the [**Scripts Folder**](scripts/)

---

## Initial Setup

- To create and use your own test accounts, you will need to install Python. It should come with Pip for handling external library installations. To work with Ethereum accounts and sending transactions, you need the library web3.

    ```bash
    pip install web3
    ```

- The make an account, you need to create an Account object, and then you can read its address and private key.

    ```
    acct1 = Account.create()
    print("Sender Address:", acct1.address)
    print("Sender Private Key:", acct1.key.hex())
    ```

- **Be Sure to save the private key somewhere after creating the account. There will be no other way to get it after seeing the output for creating the account.**

- In our case, the simplest way to send ETH is through a public node. The execution client Geth and the consensus client for carrying out transactions can be managed through sites like https://ethereum-sepolia.publicnode.com which eliminates the need to run Geth or a consensus client locally.
- When you have the public key for an account, you can view its balance in ETH. First, you need to establish a connection to your public node.

    ```
    w3 = Web3(Web3.HTTPProvider("https://ethereum-sepolia.publicnode.com"))
    ```

- With the address of a given account, you can print out their balance in ETH. Naturally, newly created accounts will have 0 ETH.

    ```
    address1 = "0x6CA38c708c1F82eAED6520bEA36a224411297cda"

    balance1_wei = w3.eth.get_balance(address1)
    balance1_eth = w3.from_wei(balance1_wei, 'ether')

    print(f"Account 1 ({address1}) balance: {balance1_eth} ETH")
    ```

**If you want free ETH for use in a testnet like Sepolia, you can go to [this site](https://sepolia-faucet.pk910.de/)**

## Sending Ethereum

- To send ETH between two accounts is also straightforward. You need a connection to a public node, your account's public and private key, and the public key of the recipient.

    ```
    # basic example
    w3 = Web3(Web3.HTTPProvider("https://ethereum-sepolia.publicnode.com"))

    sender_address = "0x6CA38c708c1F82eAED6520bEA36a224411297cda"
    receiver_address = "0xb91545c1A71c4E55c11a9ee71f6AD0c65AD809e4"
    private_key = "eaa3c90bd0f998caaa970032da17758a9cf41d47fadec2203b3927e3331ae50b"
    ```

- to create a transaction, you need to construct a python dictionary with a nonce, the recipient's public key, the amount of ETH you with to send, the amount of gas, the gas price, and the ID number for the blockchain the transaction is being conducted on. Below is a basic example of a transaction.

    ```
    tx = {
    'nonce': w3.eth.get_transaction_count(sender_address, 'pending'),
    'to': "0xb91545c1A71c4E55c11a9ee71f6AD0c65AD809e4",
    'value': w3.to_wei(0.01, 'ether'),
    'gas': 21000,
    'gasPrice': w3.to_wei(100, 'gwei'),
    'chainId': 11155111  # Sepolia chain ID
    }
    ```

- all that's left to do is sign and send the transaction. A hash is returned to you that can be inputted [**here**](https://sepolia.etherscan.io/) to view its status. Once it's done you can check the balance again to see the resulting transfer.

    ```
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    print("✅ Transaction sent!") # 0.01 ETH (sent) + 0.0021 ETH (fee) = 0.0121 ETH
    print("🔗 TX Hash:", tx_hash.hex())
    ```