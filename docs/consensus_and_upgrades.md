# Analysis: The Merge & EIP-1559 in Ethereum and Geth

## EIP-1559 – Fee Market Reform

### Motivation

Ethereum’s original gas fee mechanism was based on a first-price auction, where users bid by specifying a `gasPrice`. Miners prioritized the most profitable transactions (the ones with the highest bids), creating inefficiencies:

- Users often overpaid to ensure inclusion.
- Users unfamiliar with fee markets might wait indefinitely for confirmation during congestion.
- Fee estimation was unintuitive and worsened user experience.

### Goals of EIP-1559

EIP-1559, implemented in the London Hard Fork, was designed to:

- Make transaction fees more predictable.
- Automate the fee estimation process, improving wallet UX.
- Introduce dynamic block sizes by adjusting gas limits.
- Create a deflationary pressure on ETH by burning base fees.
- Ensure miner fairness through optional miner tips (`priorityFee`).

### Important Concepts

- Base fee = mandatory per-gas fee, dynamically adjusted per block based on network demand.
- Priority fee (tip) = optional incentive to miners to prioritize the transaction.
- Max fee (fee cap) = maximum fee user is willing to pay, allowing users to cap their spending.
- Fee burn = the base fee is burned, removing it from circulation permanently.

The network aims to achieve a 50% equilibrium:

- If block gas usage > 50% capacity, the base fee increases.
- If block gas usage < 50%, the base fee decreases.
- Max block gas increased from 12.5M to 25M.

### Geth Codebase Integration

EIP-1559 logic is handled in the Geth codebase under:

- [`core/txpool/txpool.go`](https://github.com/ethereum/go-ethereum/blob/master/core/txpool/txpool.go): Transaction prioritization considers `gasTip`.
- [`core/types/transaction.go`](https://github.com/ethereum/go-ethereum/blob/master/core/types/transaction.go): Defines new `DynamicFeeTx` type to support EIP-1559 fields (`MaxFeePerGas`, `MaxPriorityFeePerGas`).
- [`core/state_transition.go`](https://github.com/ethereum/go-ethereum/blob/master/core/state_transition.go): Fee burning logic (burned by omission) and gas accounting.
- [`consensus/misc/eip1559/eip1559.go`](https://github.com/ethereum/go-ethereum/blob/master/consensus/eip1559/eip1559.go): Dynamic base fee and block gas limit calculations.

---

## The Merge: Ethereum's Transition to Proof of Stake

### Background

Pre-Merge, Ethereum ran two parallel chains:

- **Ethereum Mainnet (Eth1)**: Used Proof of Work (PoW) for consensus.
- **Beacon Chain (Eth2)**: Ran Proof of Stake (PoS) but did not process transactions.

### What Changed

The Merge combined the execution layer (Eth1) with the consensus layer (Beacon Chain) into a unified PoS Ethereum chain.

- Eliminated energy-intensive mining.
- Reduced energy usage by ~99.95%.
- Enabled staking-based consensus for security.

The Merge was triggered when the chain hit a pre-determined terminal total difficulty (TTD), signaling the switchover from PoW to PoS.

### Geth Codebase Integration

The Merge affected multiple areas of Geth:

- [`consensus/ethash/`](https://github.com/ethereum/go-ethereum/tree/master/consensus/ethash/):
  - PoW logic was deprecated.
  - PoS fork choice and block validation are now delegated to the Consensus Layer (CL).
- [`eth/handler.go`](https://github.com/ethereum/go-ethereum/blob/master/eth/handler.go): Manages p2p messages between execution and consensus layers.
- [`core/blockchain.go`](https://github.com/ethereum/go-ethereum/blob/master/core/blockchain.go): Updated to support externalized fork choice updates.

### Post-Merge Behavior in Geth

- Geth no longer performs consensus as it relies on consensus clients(like Lighthouse, Prysm, or Teku) for fork choice.
- Execution payloads are verified and processed, but block production and validation are led by the CL.
- Validators propose blocks and attach execution payloads that Geth verifies and applies to the state.

---
