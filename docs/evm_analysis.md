# EVM Contract Creation & Execution Analysis

This document analyzes the contract creation and execution mechanisms in Ethereum's Virtual Machine as implemented in [`core/vm/evm.go`](https://github.com/ethereum/go-ethereum/blob/master/core/vm/evm.go#L413). We'll examine the key functions responsible for contract creation(`create()`, `Create()`, `Create2()`) and contract execution(`Call()`, `CallCode()`, `DelegateCall()`, `StaticCall()`).

## Contract Creation

Ethereum supports two ways to create contracts: standard creation using the `CREATE` opcode and deterministic creation using `CREATE2`. Both call the internal `create()` function.

### Shared Logic `create()`

```go
func (evm *EVM) create(
    caller common.Address,
    code []byte,
    gas uint64,
    value *uint256.Int,
    address common.Address,
    typ OpCode) (
        ret []byte,
        createAddress common.Address,
        leftOverGas uint64,
        err error)
```

#### Input Parameters

- `caller`: address that initiates contract creation
- `code`: initialization code for the new contract
- `gas`: gas provided for creation
- `value`: Amount of Ether sent to the new contract
- `address`: target contract address
- `typ`: `CREATE` or `CREATE2` opcode

#### Return Values

- `ret`: result from running initialization code
- `createAddress`: address where the contract was created
- `leftOverGas`: unused gas
- `err`: any error during creation

### Creation Flow

1. **Initial Setup**:

   - Captures tracing information if a tracer is configured:
     ```go
     if evm.Config.Tracer != nil {
         evm.captureBegin(evm.depth, typ, caller, address, code, gas, value.ToBig())
         defer func(startGas uint64) {
             evm.captureEnd(evm.depth, startGas, leftOverGas, ret, err)
         }(gas)
     }
     ```
   - Performs depth check to prevent stack overflow attacks:
     ```go
     if evm.depth > int(params.CallCreateDepth) {
         return nil, common.Address{}, gas, ErrDepth
     }
     ```

2. **Validation Checks**:

   - Ensures the caller has sufficient balance:
     ```go
     if !evm.Context.CanTransfer(evm.StateDB, caller, value) {
         return nil, common.Address{}, gas, ErrInsufficientBalance
     }
     ```
   - Verifies nonce overflow protection and updates the caller's nonce:
     ```go
     nonce := evm.StateDB.GetNonce(caller)
     if nonce+1 < nonce {
         return nil, common.Address{}, gas, ErrNonceUintOverflow
     }
     evm.StateDB.SetNonce(caller, nonce+1, tracing.NonceChangeContractCreator)
     ```

3. **EIP-4762 Support**(Verkle Trees):

   - Charges gas for contract creation pre-checks:
     ```go
     if evm.chainRules.IsEIP4762 {
         statelessGas := evm.AccessEvents.ContractCreatePreCheckGas(address)
         if statelessGas > gas {
             return nil, common.Address{}, 0, ErrOutOfGas
         }
         if evm.Config.Tracer != nil && evm.Config.Tracer.OnGasChange != nil {
             evm.Config.Tracer.OnGasChange(gas, gas-statelessGas, tracing.GasChangeWitnessContractCollisionCheck)
         }
         gas = gas - statelessGas
     }
     ```

4. **Collision Check**:

   - Ensures no existing contract is at the target address by checking nonce, code hash, and storage root:
     ```go
     contractHash := evm.StateDB.GetCodeHash(address)
     storageRoot := evm.StateDB.GetStorageRoot(address)
     if evm.StateDB.GetNonce(address) != 0 ||
         (contractHash != (common.Hash{}) && contractHash != types.EmptyCodeHash) ||
         (storageRoot != (common.Hash{}) && storageRoot != types.EmptyRootHash) {
         // ...
         return nil, common.Address{}, 0, ErrContractAddressCollision
     }
     ```

5. **State Management**:

   - Creates a snapshot and sets up the account:

     ```go
     snapshot := evm.StateDB.Snapshot()
     if !evm.StateDB.Exist(address) {
         evm.StateDB.CreateAccount(address)
     }
     evm.StateDB.CreateContract(address)

     if evm.chainRules.IsEIP158 {
         evm.StateDB.SetNonce(address, 1, tracing.NonceChangeNewContract)
     }
     ```

6. **Ether Transfer**:

   - Charges gas for contract initialization in Verkle mode:
     ```go
     if evm.chainRules.IsEIP4762 {
         statelessGas := evm.AccessEvents.ContractCreateInitGas(address)
         if statelessGas > gas {
             return nil, common.Address{}, 0, ErrOutOfGas
         }
         // ...
         gas = gas - statelessGas
     }
     ```
   - Transfers the specified Ether value from caller to contract:
     ```go
     evm.Context.Transfer(evm.StateDB, caller, address, value)
     ```

7. **Run Initialization Code**

   - Creates a new contract object with code and gas:
     ```go
     contract := NewContract(caller, address, value, gas, evm.jumpDests)
     contract.SetCallCode(common.Hash{}, code)
     contract.IsDeployment = true
     ```
   - Executes the initialization code:

     ```go
     ret, err = evm.initNewContract(contract, address)
     ```

   The `initNewContract` method runs the contract’s initialization code. It checks that the code meets size limits and does not contain any forbidden opcodes. It then deducts the required gas for storing the code and writes the resulting bytecode to the state.

### Standard Contract Creatio `Create()`

```go
func (evm *EVM) Create(caller common.Address, code []byte, gas uint64, value *uint256.Int) (ret []byte, contractAddr common.Address, leftOverGas uint64, err error) {
    contractAddr = crypto.CreateAddress(caller, evm.StateDB.GetNonce(caller))
    return evm.create(caller, code, gas, value, contractAddr, CREATE)
}
```

- Uses sender's address and current nonce to compute the contract address.
- Address is sequential and predictable.

### Deterministic Contract Creation `Create2()`

```go
func (evm *EVM) Create2(caller common.Address, code []byte, gas uint64, endowment *uint256.Int, salt *uint256.Int) (ret []byte, contractAddr common.Address, leftOverGas uint64, err error) {
    inithash := crypto.HashData(evm.interpreter.hasher, code)
    contractAddr = crypto.CreateAddress2(caller, salt.Bytes32(), inithash[:])
    return evm.create(caller, code, gas, endowment, contractAddr, CREATE2)
}
```

- Computes sender's address, a sender-chosen salt, and the hash of the initialization code
- Allows address predictability without relying on sender’s nonce

---

## Contract Execution

Ethereum supports four types of external contract interaction:

1. Standard call CALL
2. Code execution with caller's context CALLCODE
3. Delegated call execution DELEGATECALL
4. Read-only call STATICCALL

### Standard Call `Call()`

The standard CALL opcode lets a contract interact with another contract or account. The called code runs in the callee’s context. The caller can send Ether and trigger state changes.

### Method Signature

```go
func (evm *EVM) Call(caller common.Address, addr common.Address, input []byte, gas uint64, value *uint256.Int) (ret []byte, leftOverGas uint64, err error)
```

### Execution Flow

1. **Validation**

   The EVM checks for stack depth overflow and sufficient balance:

   ```go
   if evm.depth > int(params.CallCreateDepth) {
       return nil, gas, ErrDepth
   }
   if !value.IsZero() && !evm.Context.CanTransfer(evm.StateDB, caller, value) {
       return nil, gas, ErrInsufficientBalance
   }
   ```

2. **Snapshot**

   The EVM saves a snapshot of the current state in case it needs to revert:

   ```go
   snapshot := evm.StateDB.Snapshot()
   ```

3. **Account Creation**(if needed):

   If the target account does not exist, the EVM may create it:

   ```go
   if !evm.StateDB.Exist(addr) {
       if !isPrecompile && evm.chainRules.IsEIP4762 && !isSystemCall(caller) {
           wgas := evm.AccessEvents.AddAccount(addr, false)
           if gas < wgas {
               evm.StateDB.RevertToSnapshot(snapshot)
               return nil, 0, ErrOutOfGas
           }
           gas -= wgas
       }

       if !isPrecompile && evm.chainRules.IsEIP158 && value.IsZero() {
           return nil, gas, nil
       }
       evm.StateDB.CreateAccount(addr)
   }
   ```

4. **Value Transfer**:

   The EVM moves Ether from the caller to the callee:

   ```go
   evm.Context.Transfer(evm.StateDB, caller, addr, value)
   ```

5. **Code Execution**:

   - If the target is a precompiled contract:
     ```go
     if isPrecompile {
         ret, gas, err = RunPrecompiledContract(p, input, gas, evm.Config.Tracer)
     }
     ```
   - If the target is a regular contract:
     ```go
     else {
         code := evm.resolveCode(addr)
         if len(code) == 0 {
             ret, err = nil, nil // gas is unchanged
         } else {
             contract := NewContract(caller, addr, value, gas, evm.jumpDests)
             contract.IsSystemCall = isSystemCall(caller)
             contract.SetCallCode(evm.resolveCodeHash(addr), code)
             ret, err = evm.interpreter.Run(contract, input, false)
             gas = contract.Gas
         }
     }
     ```

### CallCode Execution `CallCode()`

```go
func (evm *EVM) CallCode(caller common.Address, addr common.Address, input []byte, gas uint64, value *uint256.Int) (ret []byte, leftOverGas uint64, err error)
```

The CallCode method runs a target contract’s code in the caller’s own context, therefore allowing logic reuse while applying all storage and balance changes to the caller’s account.

```go
// In Call:
contract := NewContract(caller, addr, value, gas, evm.jumpDests)

// In CallCode:
contract := NewContract(caller, caller, value, gas, evm.jumpDests)
```

### Delegated Execution `DelegateCall()`

```go
func (evm *EVM) DelegateCall(originCaller common.Address, caller common.Address, addr common.Address, input []byte, gas uint64, value *uint256.Int) (ret []byte, leftOverGas uint64, err error) {
    // ...
}
```

DelegateCall preserves the original caller relationship, therefore allowing for more flexible library patterns.

```go
// In CallCode:
contract := NewContract(caller, caller, value, gas, evm.jumpDests)

// In DelegateCall:
contract := NewContract(originCaller, caller, value, gas, evm.jumpDests)
```

### Static Execution `StaticCall()`

```go
func (evm *EVM) StaticCall(caller common.Address, addr common.Address, input []byte, gas uint64) (ret []byte, leftOverGas uint64, err error) {
    // ...
}
```

StaticCall executes a contract call without allowing state modifications, ensuring read-only operations. This call type is used for read-only operations.

```go
// In Call:
ret, err = evm.interpreter.Run(contract, input, false)

// In StaticCall:
ret, err = evm.interpreter.Run(contract, input, true)
```

The `true` parameter in `Run()` enforces read-only mode, ensuring that any state-modifying operations are reverted and have no lasting effect.

### Common Patterns

We observed that: all methods include tracer hooks for debugging or monitoring:

```go
if evm.Config.Tracer != nil {
    evm.captureBegin(evm.depth, CALL_TYPE, caller, addr, input, gas, value.ToBig())
    defer func(startGas uint64) {
        evm.captureEnd(evm.depth, startGas, leftOverGas, ret, err)
    }(gas)
}
```

All methods check if the target is a precompiled contract:

```go
if p, isPrecompile := evm.precompile(addr); isPrecompile {
    ret, gas, err = RunPrecompiledContract(p, input, gas, evm.Config.Tracer)
}
```

For contract creation, the `Call` method is the only one that may create a new account if needed:

```go
if !evm.StateDB.Exist(addr) {
    // ...
    evm.StateDB.CreateAccount(addr)
}
```
