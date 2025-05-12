# Ethereum Transaction Processing Flow

This examines how Ethereum processes transactions from initial signing to final inclusion in the blockchain, with a focus on the `StateProcessor` implementation in Geth's core package.

## Transaction Lifecycle

### 1. Transaction Initiation

- User signs transaction with private key (e.g., via MetaMask)
- Transaction sent to Ethereum node via JSON-RPC (`eth_sendTransaction` or `eth_sendRawTransaction`)

### 2. Transaction Reception & Validation

- Execution client (Geth) receives transaction and:
  - Verifies signature, nonce, and sufficient balance for gas
  - If valid, adds to mempool as pending
- Node broadcasts transaction to peers
- Other nodes receive and add to their mempools

### 3. Block Creation

- Beacon chain (consensus client) selects validator for the current slot (every 12s)
- Selected validator proposes block including pending transactions
- Consensus client packages into Beacon Block and broadcasts

### 4. Transaction Execution

- **Core processing happens in `StateProcessor.Process`**
- For each transaction, state transitions are applied according to EVM rules

### 5. Finalization

- Block is broadcast, verified, and ultimately finalized
- Transaction becomes permanent part of the Ethereum blockchain

## `StateProcessor` Structure

The `StateProcessor` is defined as follows:

```go
// StateProcessor implements Processor.
type StateProcessor struct {
    config *params.ChainConfig // Chain configuration options
    chain  *HeaderChain        // Canonical header chain
}

// NewStateProcessor initialises a new StateProcessor.
func NewStateProcessor(config *params.ChainConfig, chain *HeaderChain) *StateProcessor {
    return &StateProcessor{
        config: config,
        chain:  chain,
    }
}
```

This structure maintains references to:

- Chain configuration options(`config`) - containing parameters like fork blocks
- Canonical header chain(`chain`) - providing access to block header data

## `StateProcessor.Process`

The `StateProcessor.Process` method in [`core/state_processor.go`](https://github.com/ethereum/go-ethereum/blob/master/core/state_processor.go) is the core of transaction execution, responsible for processing the state changes. It is defined as:

```go
func (p *StateProcessor) Process(block *types.Block, statedb *state.StateDB, cfg vm.Config) (*ProcessResult, error) {
    var (
        receipts    types.Receipts
        usedGas     = new(uint64)
        header      = block.Header()
        blockHash   = block.Hash()
        blockNumber = block.Number()
        allLogs     []*types.Log
        gp          = new(GasPool).AddGas(block.GasLimit())
    )
```

The method begins by initializing key variables:

- `receipts` to collect transaction receipts
- `usedGas` to track cumulative gas consumption
- Block information (`header`, `blockHash`, `blockNumber`)
- `allLogs` to collect transaction logs
- Gas pool (`gp`) initialized with the block's gas limit

### Hard Fork Handling

```go
    // Mutate the block and state according to any hard-fork specs
    if p.config.DAOForkSupport && p.config.DAOForkBlock != nil && p.config.DAOForkBlock.Cmp(block.Number()) == 0 {
        misc.ApplyDAOHardFork(statedb)
    }
```

Before processing transactions, the code checks for and applies hard fork rules. Here, it specifically checks for the DAO fork, a historical hard fork that recovered funds after the 2016 DAO attack.

### EVM Context Setup

```go
    var (
        context vm.BlockContext
        signer  = types.MakeSigner(p.config, header.Number, header.Time)
    )

    // Apply pre-execution system calls.
    var tracingStateDB = vm.StateDB(statedb)
    if hooks := cfg.Tracer; hooks != nil {
        tracingStateDB = state.NewHookedState(statedb, hooks)
    }
    context = NewEVMBlockContext(header, p.chain, nil)
    evm := vm.NewEVM(context, tracingStateDB, p.config, cfg)
```

The code then:

1. Creates a transaction signer based on the block's properties
2. Sets up tracing if configured
3. Creates an Ethereum Virtual Machine (EVM) instance with the block context

### Pre-Transaction System Calls

```go
    if beaconRoot := block.BeaconRoot(); beaconRoot != nil {
        ProcessBeaconBlockRoot(*beaconRoot, evm)
    }
    if p.config.IsPrague(block.Number(), block.Time()) || p.config.IsVerkle(block.Number(), block.Time()) {
        ProcessParentBlockHash(block.ParentHash(), evm)
    }
```

Some protocol operations are executed before transaction processing:

- EIP-4788: Beacon block root processing
- EIP-2935/7709: Parent block hash processing(for Prague or Verkle forks)

### Transaction Processing Loop

The core transaction processing occurs in the following loop:

```go
    // Iterate over and process the individual transactions
    for i, tx := range block.Transactions() {
        msg, err := TransactionToMessage(tx, signer, header.BaseFee)
        if err != nil {
            return nil, fmt.Errorf("could not apply tx %d [%v]: %w", i, tx.Hash().Hex(), err)
        }
        statedb.SetTxContext(tx.Hash(), i)

        receipt, err := ApplyTransactionWithEVM(msg, gp, statedb, blockNumber, blockHash, tx, usedGas, evm)
        if err != nil {
            return nil, fmt.Errorf("could not apply tx %d [%v]: %w", i, tx.Hash().Hex(), err)
        }
        receipts = append(receipts, receipt)
        allLogs = append(allLogs, receipt.Logs...)
    }
```

For each transaction:

1. Convert the transaction to a message format with `TransactionToMessage`
2. Set the transaction context in the state database
3. Apply the transaction using `ApplyTransactionWithEVM`
4. Collect the receipt and logs

### Post-Transaction Processing

```go
    // Read requests if Prague is enabled.
    var requests [][]byte
    if p.config.IsPrague(block.Number(), block.Time()) {
        requests = [][]byte{}
        // EIP-6110
        if err := ParseDepositLogs(&requests, allLogs, p.config); err != nil {
            return nil, err
        }
        // EIP-7002
        if err := ProcessWithdrawalQueue(&requests, evm); err != nil {
            return nil, err
        }
        // EIP-7251
        if err := ProcessConsolidationQueue(&requests, evm); err != nil {
            return nil, err
        }
    }
```

After transactions are processed, more protocol-specific operations may execute:

- EIP-6110: Parsing deposit logs
- EIP-7002: Processing the withdrawal queue
- EIP-7251: Processing the consolidation queue

### Block Finalization

```go
    // Finalize the block, applying any consensus engine specific extras (e.g. block rewards)
    p.chain.engine.Finalize(p.chain, header, tracingStateDB, block.Body())

    return &ProcessResult{
        Receipts: receipts,
        Requests: requests,
        Logs:     allLogs,
        GasUsed:  *usedGas,
    }, nil
}
```

Finally:

1. The block is finalized with consensus engine-specific operations (like distributing block rewards)
2. A `ProcessResult` is returned with receipts, requests, logs, and total gas used

## References

- [Transaction Lifecycle in Ethereum](https://medium.com/blockchannel/life-cycle-of-an-ethereum-transaction-e5c66bae0f6e)
- [Ethereum Block Processing Explained](https://ethereum.org/en/developers/docs/blocks/)
- [EIP-4788: Beacon block root in the EVM](https://eips.ethereum.org/EIPS/eip-4788)
- [EIP-2935: Save historical block hashes in state](https://eips.ethereum.org/EIPS/eip-2935)
- [Ethereum Prague Network Upgrade Overview](https://crypto.com/en/university/ethereum-pectra-prague-electra-upgrade)
