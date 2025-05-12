# Ethereum Service Registration in Geth

This section analyzes how Ethereum services are registered and initialized in the Geth client, focusing on the core component setup defined in [`eth/backend.go`](https://github.com/ethereum/go-ethereum/blob/master/eth/backend.go).

## Service Registration Overview

After makeConfigNode creates the base node infrastructure, Geth registers its core services using `stack.Register()`. The core registration is the Ethereum backend itself, which is created and wired to the node through `eth.New()`. This function connects all essential components that make up a functioning Ethereum node.

## Breakdown of `eth.New()`

The `eth.New()` function in `eth/backend.go` is responsible for creating and connecting all core Ethereum components:

```go
func New(stack *node.Node, config *ethconfig.Config) (*Ethereum, error) {
    // ...
}
```

### 1. Configuration Validation and Sanitization

The function begins with validating the configuration parameters to ensure they're compatible and sane:

```go
if !config.SyncMode.IsValid() {
    return nil, fmt.Errorf("invalid sync mode %d", config.SyncMode)
}
if !config.HistoryMode.IsValid() {
    return nil, fmt.Errorf("invalid history mode %d", config.HistoryMode)
}
if config.Miner.GasPrice == nil || config.Miner.GasPrice.Sign() <= 0 {
    log.Warn("Sanitizing invalid miner gas price", "provided", config.Miner.GasPrice, "updated", ethconfig.Defaults.Miner.GasPrice)
    config.Miner.GasPrice = new(big.Int).Set(ethconfig.Defaults.Miner.GasPrice)
}
```

This ensures that all critical configuration settings are valid before proceeding with node initialization.

### 2. Database Initialization

The function opens the chain database with appropriate caching parameters:

```go
chainDb, err := stack.OpenDatabaseWithFreezer("chaindata", config.DatabaseCache, config.DatabaseHandles, config.DatabaseFreezer, "eth/db/chaindata/", false)
if err != nil {
    return nil, err
}
```

This database will store the blockchain data, including blocks, state, and receipts.

### 3. Chain Configuration Loading

It loads the chain configuration from either the database or genesis block:

```go
chainConfig, _, err := core.LoadChainConfig(chainDb, config.Genesis)
if err != nil {
    return nil, err
}
```

The chain configuration defines parameters like chain ID, block rewards, fork blocks, and EIPs that are active.

### 4. Consensus Engine Creation

Based on the chain configuration, the appropriate consensus engine is created:

```go
engine, err := ethconfig.CreateConsensusEngine(chainConfig, chainDb)
if err != nil {
    return nil, err
}
```

This could be ethash(PoW), clique(PoA), or the Engine API interface for proof-of-stake.

### 5. Core Ethereum Object Assembly

The function creates the main Ethereum struct that will hold references to all components:

```go
eth := &Ethereum{
    config:          config,
    chainDb:         chainDb,
    eventMux:        stack.EventMux(),
    accountManager:  stack.AccountManager(),
    engine:          engine,
    networkID:       networkID,
    gasPrice:        config.Miner.GasPrice,
    p2pServer:       stack.Server(),
    discmix:         enode.NewFairMix(0),
    shutdownTracker: shutdowncheck.NewShutdownTracker(chainDb),
}
```

### 6. Blockchain Initialization

The function creates the blockchain object, which manages the chain of blocks and state transitions:

```go
eth.blockchain, err = core.NewBlockChain(chainDb, cacheConfig, config.Genesis, &overrides, eth.engine, vmConfig, &config.TransactionHistory)
if err != nil {
    return nil, err
}
```

The blockchain component is responsible for:

- Block validation and execution
- State management
- Chain reorganization handling
- Consensus rule enforcement

### 7. Filter Maps for Log Indexing

It initializes the filter maps system for efficient log queries:

```go
eth.filterMaps = filtermaps.NewFilterMaps(chainDb, chainView, historyCutoff, finalBlock, filtermaps.DefaultParams, fmConfig)
```

This component enables efficient event log subscription and filtering.

### 8. Transaction Pool Setup

The function initializes the transaction pool, which manages pending transactions:

```go
legacyPool := legacypool.New(config.TxPool, eth.blockchain)
blobPool := blobpool.New(config.BlobPool, eth.blockchain, legacyPool.HasPendingAuth)
eth.txPool, err = txpool.New(config.TxPool.PriceLimit, eth.blockchain, []txpool.SubPool{legacyPool, blobPool})
```

The transaction pool handles:

- Transaction validation and sorting
- Gas price-based prioritization
- Local transaction management
- Transaction propagation to peers

### 9. Network Handler Initialization

It creates the protocol handler for P2P communication:

```go
eth.handler, err = newHandler(&handlerConfig{
    NodeID:         eth.p2pServer.Self().ID(),
    Database:       chainDb,
    Chain:          eth.blockchain,
    TxPool:         eth.txPool,
    Network:        networkID,
    Sync:           config.SyncMode,
    BloomCache:     uint64(cacheLimit),
    EventMux:       eth.eventMux,
    RequiredBlocks: config.RequiredBlocks,
})
```

The handler manages:

- Peer connections and protocol handshakes
- Block synchronization
- Transaction propagation
- Chain information exchange

### 10. Miner Component Setup

It initializes the miner/block producer component:

```go
eth.miner = miner.New(eth, config.Miner, eth.engine)
eth.miner.SetExtra(makeExtraData(config.Miner.ExtraData))
eth.miner.SetPrioAddresses(config.TxPool.Locals)
```

The miner is responsible for:

- Block creation
- Transaction selection
- Fee recipient management
- Block sealing (via consensus engine)

### 11. API Backend Registration

It creates the API backend that will handle RPC requests:

```go
eth.APIBackend = &EthAPIBackend{stack.Config().ExtRPCEnabled(), stack.Config().AllowUnprotectedTxs, eth, nil}
eth.APIBackend.gpo = gasprice.NewOracle(eth.APIBackend, config.GPO, config.Miner.GasPrice)
```

### 12. API Service Registration

Finally, the node calls

```go
stack.RegisterAPIs(eth.APIs())
stack.RegisterProtocols(eth.Protocols())
stack.RegisterLifecycle(eth)
```

to wire up all of its services, exposing the Ethereum JSON-RPC interface(under the eth namespace) along with the Miner, Admin, Debug, Network, and any consensus-specific APIs.
