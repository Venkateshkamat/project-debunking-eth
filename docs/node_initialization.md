# Ethereum Node Initialization in Geth

This document analyzes how Geth transforms command-line flags and configuration files into a fully operational Ethereum node. It explains the startup process that prepares the node to sync the blockchain, process transactions, and serve API requests.

The main entry point for execution client setup is:
`func makeFullNode(ctx *cli.Context) *node.Node`, and is located in [`cmd/geth/config.go`](https://github.com/ethereum/go-ethereum/blob/master/cmd/geth/config.go).

## Breakdown of `makeFullNode(ctx)`

### 1. Call `makeConfigNode(ctx)`

`makeFullNode(ctx)` starts by calling `makeConfigNode(ctx)` to build base node.

```go
stack, cfg := makeConfigNode(ctx)
```

This line initializes the core node and configuration where:

- `stack` is a `*node.Node` instance that provides the service container for Ethereum and other modules.
- `cfg` is a gethConfig struct that includes Ethereum-specific settings such as chain rules, consensus configs, database paths, and network options.

Internally, makeConfigNode() builds the base node instance and loads the configuration.

### 2. Apply Chain Rule Overrides

Immediately after creating the config, Geth applies optional hard fork overrides:

```go
if ctx.IsSet(utils.OverridePrague.Name) {
    v := ctx.Uint64(utils.OverridePrague.Name)
    cfg.Eth.OverridePrague = &v
}
if ctx.IsSet(utils.OverrideVerkle.Name) {
    v := ctx.Uint64(utils.OverrideVerkle.Name)
    cfg.Eth.OverrideVerkle = &v
}
```

These overrides allow custom fork block numbers via CLI flags like `--overridePrague` and `--overrideVerkle`. This is useful for testing specific upgrade transitions, development environments, or custom networks with modified fork schedules

### 3. Setup Metrics

```go
utils.SetupMetrics(&cfg.Metrics)
```

If metrics are enabled with CLI flags, Geth calls `utils.SetupMetrics()` to export Prometheus-style metrics. Geth also generates runtime metadata. This includes architecture, operating system, and protocol versions.

### 4. Register Ethereum Backend

```go
backend, eth := utils.RegisterEthService(stack, &cfg.Eth)
```

The `RegisterEthService()` function adds the full Ethereum protocol stack to the node. It registers:

- Blockchain state and execution engine
- Transaction pool
- Chain synchronization mechanisms
- Miner or validator(if enabled)
- P2P protocol manager
- RPC APIs via internal `RegisterAPIs()` calls

This is where the core Ethereum functionality is integrated into the node.

### 5. Configure Log Filter RPC API

```go
filterSystem := utils.RegisterFilterAPI(stack, backend, &cfg.Eth)
```

This initializes and registers the filtering system used by both the RPC API and GraphQL. It allows clients to:

- Subscribe to logs
- Filter blockchain events
- Receive real-time notifications

### 6. Service Registration

The remainder of the function conditionally initializes additional services based on CLI flags:

#### 6.1. GraphQL API

```go
if ctx.IsSet(utils.GraphQLEnabledFlag.Name) {
    utils.RegisterGraphQLService(stack, backend, filterSystem, &cfg.Node)
}
```

When the GraphQL flag is enabled, Geth sets up a GraphQL endpoint that provides an alternative query interface to the blockchain.

#### 6.2. Ethstats Monitoring

```go
if cfg.Ethstats.URL != "" {
    utils.RegisterEthStatsService(stack, backend, cfg.Ethstats.URL)
}
```

This registers a monitoring service that reports node statistics to an ethstats server, which is commonly used for network monitoring dashboards.

#### 6.3. Sync Testing

```go
if ctx.IsSet(utils.SyncTargetFlag.Name) {
    // Register full-sync tester
}
```

This creates a testing service to validate synchronization against a specific target block hash.

### 7. Consensus Mode Configuration

The final section configures the consensus mechanism based on the operating mode:

#### 7.1. Developer Mode

```go
if ctx.IsSet(utils.DeveloperFlag.Name) {
    // Start dev mode with simulated beacon
}
```

When running in developer mode, Geth creates a simulated beacon chain for testing post-merge functionality locally.

#### 7.2. Beacon Light Client Mode

```go
else if ctx.IsSet(utils.BeaconApiFlag.Name) {
    // Start blsync mode
}
```

This mode connects to a beacon light client to receive consensus updates.

#### 7.3. Standard Consensus Engine API

```go
else {
    // Launch the engine API for interacting with external consensus client
    err := catalyst.Register(stack, eth)
    if err != nil {
        utils.Fatalf("failed to register catalyst service: %v", err)
    }
}
```

In normal operation, Geth registers the Engine API to communicate with an external consensus client (like Prysm, Lighthouse, etc.) following the post-merge architecture.

---

## Starting the Node

Once the node is fully initialized by `makeFullNode()`, it's passed to `StartNode()`, which launches the node and opens all registered network services and RPC endpoints.

```go
func StartNode(ctx *cli.Context, stack *node.Node, isConsole bool)
```

This function starts the actual node operation, at which point Geth begins:

- Discovering peers
- Synchronizing the blockchain
- Processing transactions
- Serving API requests
