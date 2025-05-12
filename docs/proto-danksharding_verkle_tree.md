# Proto-Danksharding and Verkle Trees

This analysis examines Geth’s preparations for Ethereum’s next scaling phases: Proto-Danksharding(EIP-4844) and Verkle Trees, and explores their impact on Layer 2 rollups and stateless clients.

## Proto-Danksharding(EIP-4844)

Proto-Danksharding addresses major data bottlenecks by providing a dedicated layer for rollup data. It is the first step toward full sharding and its main goal is to reduce data costs for Layer 2 rollups.

- **Blob-carrying Transactions**  
  These are new transaction types. They include large “blobs” of data that are stored off-chain. The data stays available for a short time so rollups can access it. This helps lower data availability costs.

### Implementation in Geth

- [**`core/types/tx_blob.go`**](https://github.com/ethereum/go-ethereum/blob/master/core/types/tx_blob.go): Defines the `BlobTx` structure
- [**`core/types/transaction.go`**](https://github.com/ethereum/go-ethereum/blob/master/core/types/transaction.go): Implements the blob transaction type and related structures
- [**`core/types/transaction_signing.go`**](https://github.com/ethereum/go-ethereum/blob/master/core/types/transaction_signing.go): Handles blob transaction signatures
- [**`params/protocol_params.go`**](https://github.com/ethereum/go-ethereum/blob/master/params/protocol_params.go): Defines EIP-4844 constants and parameters
- [**`core/blockchain.go`**](https://github.com/ethereum/go-ethereum/blob/master/core/blockchain.go): Integrates blob transactions into block processing

---

## Verkle Trees

Verkle Trees are designed to replace the current Merkle Patricia Trie. They significantly reduce proof sizes and make stateless clients possible. This change will improve both efficiency and scalability across the Ethereum network.

### Key Improvements

- **Vector Commitments**:

  Verkle Trees use KZG commitments to aggregate many leaves into a single root. This allows efficient proof generation and verification.

- **Compact Proofs**:

  Verkle proofs reduce witness sizes from hundreds of kilobytes to less than 1 KB. This enables faster and lighter clients.

- **State Efficiency**:

  Smaller proofs and faster lookups allow light clients to operate without downloading gigabytes of state data.

### Implementation in Geth

Implementation appears to be in progress in the client code. The main focus areas are:

- **`core/state`**: Refactors state storage for vector commitments
- **`trie/`**: Implements new trie structures using KZG-based commitments

Verkle Trees are a key part of the “Verge” phase in Ethereum’s roadmap. They will enable stateless clients and speed up node synchronization. This is one of the most ambitious changes to Ethereum’s internal architecture since the Merge.

## References

- [Go-Ethereum (Geth) Repository](https://github.com/ethereum/go-ethereum)
- [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)
- [Ethereum Foundation - Proto-Danksharding FAQ](https://notes.ethereum.org/@vbuterin/proto_danksharding_faq)
- [Vitalik Buterin: Why Verkle Trees](https://vitalik.eth.limo/general/2021/06/18/verkle.html)
- [Ethereum Improvement Proposals](https://github.com/ethereum/EIPs)
- [Dankrad Feist: KZG polynomial commitments](https://dankradfeist.de/ethereum/2020/06/16/kate-polynomial-commitments.html)
