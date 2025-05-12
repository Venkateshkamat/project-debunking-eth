# Debunking Ethereum

A deep dive into the Ethereum protocol and codebase using [Geth (go-ethereum)](https://github.com/ethereum/go-ethereum).  
We analyze how Ethereum works under the hood, including the transaction lifecycle, consensus changes, and deploying real transactions.

This project is inspired by “Debunking Bitcoin,” but extended to Ethereum, with a focus on understanding the Geth codebase, transaction/state management, and the post-Merge consensus system.

---

## Project Structure

We explored Ethereum in four key areas:

### 1. **Geth Codebase Overview**

- Investigated startup flow and how Geth initializes modules like `eth/`, `p2p/`, and `cmd/`.
- Mapped core module responsibilities:
  - `core/`: Blockchain state and transaction processing
  - `eth/`: Ethereum protocol implementation
  - `p2p/`: Network layer
  - `rpc/`: Exposes RPC APIs

### 2. **State Management & Transactions**

- Traced the transaction lifecycle from submission to block inclusion and execution.
- Analyzed source files such as `tx_pool.go`, `blockchain.go`, `state_processor.go`, and `statedb.go`.
- Explained how account balances and contract storage are managed using Merkle Patricia Tries.

### 3. **Deploy & Interact**

- Set up a local development environment using Web3.py and connected to Ethereum’s Sepolia testnet.
- Deployed and interacted with a sample smart contract.
- Observed transaction state changes and gas usage.
- Scripts used:
  - `account.py`: Generates Ethereum accounts.
  - `address.py`: Checks balance of two accounts on Sepolia.
  - `transaction.py`: Sends ETH from one address to another using Web3.py.

### 4. **Consensus & Upgrades**

- Researched Ethereum’s upgrade timeline and breaking changes:
  - **The Merge** (PoW → PoS): Investigated `consensus/engine/`
  - **EIP-1559** (gas fee reform): Explained dynamic base fees and tips
  - **EIP-4844** (Proto-Danksharding): Layer 2 scalability using blobs
  - **Verkle Trees**: Upcoming change to improve state size & access

---

## How to Run the Python Scripts

1. **Install dependencies**  
   Run the following in your terminal:

   ```bash
   pip install web3
   ```

2. **Generate accounts**

   ```bash
   python account.py
   ```

3. **Check balances**

   ```bash
   python address.py
   ```

4. **Send ETH on Sepolia (make sure sender has funds)**

   ```bash
   python transaction.py
   ```

# Team Contributions

## Daniel

- **State Management & Transactions**
- [**Deploy & Interact**](/docs/deployment.md)
  - Wrote Python scripts to:
    - Generate Ethereum accounts (`account.py`)
    - Check balances on Sepolia (`address.py`)
    - Send ETH transactions using Web3.py (`transaction.py`)
  - Set up local environment (Sepolia Testnet)

---

## Venkatesh

- [**Geth Codebase Overview**](/docs/geth_code_overview.md)
  - Explored startup flow via `cmd/geth`
  - Mapped module responsibilities (`eth/`, `core/`, `p2p/`, `rpc/`)
- **State Management & Transactions**
  - Contributed to research on transaction processing and state updates

---

## Xinhao

- **State Management & Transactions**
  - Investigated Ethereum’s transaction lifecycle
  - Analyzed how transactions move from mempool to execution (`tx_pool.go`, `blockchain.go`)
  - Reviewed state structures in `state_object.go` and `state_db.go`

---

## Kathy

- **Geth Codebase Overview**
  - Investigated [Ethereum Node Initialization](docs/node_initialization.md) in `cmd/geth/config.go`
  - Explored [Service Registration](docs/service_resgistration.md) in `eth/backend.go`
  - Analyzed [Contract Creation and Execution](docs/evm_analysis.md) in `core/vm/evm.go`
- **[Transaction Processing Flow](docs/tx_processing.md)**
- **Consensus & Upgrades**
  - Researched future scaling proposals: [EIP-4844(Proto-Danksharding) & Verkle Trees](docs/proto-danksharding_verkle_tree.md)
- **Node Implementation**
  - [Running an Ethereum node on external SSD using geth and prysm](https://docs.google.com/document/d/12nJMG3LiXx2Y7UPmoq1w9bOyJGU9kCB49lgibeR_69Y/edit?usp=sharing)
  - [Create account and sign with Clef](https://docs.google.com/document/d/1nZcG6HFykAk0Q4nh4oNzgASW1vRQ2swxmDmodVms4J0/edit?usp=sharing)

---

## Becky

- [**Consensus & Upgrades**](docs/consensus_and_upgrades.md)
  - Researched and documented **The Merge** (transition from PoW to PoS)
  - Analyzed Geth's `consensus/` module
  - Explained **EIP-1559** gas fee reform and how it changed transaction behavior
    - Explored how it affected transaction execution code

---
