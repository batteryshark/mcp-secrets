# MCP Secrets JavaScript Implementation Design

## Overview
This is a JavaScript/TypeScript port of the Python `mcp_secrets` package, designed to provide secure credential management for MCP (Model Context Protocol) servers. The implementation uses **FastMCP** by punkpeye as the core framework.

## Architecture Comparison

### Python Components Analysis
The original Python implementation consists of:

1. **MCPSecretsManager** (`__init__.py`) - Main interface and orchestrator
2. **MCPSecretsStorage** (`storage.py`) - Keyring-based secure storage using Python `keyring`
3. **AsyncUIHandler** (`ui_handler.py`) - Cross-platform native dialog spawning
4. **fetch_secrets** (`fetcher.py`) - Async credential elicitation with verification codes
5. **Native Binaries** (`secrets_dialog/`) - Rust-compiled cross-platform UI dialogs

### JavaScript Implementation Strategy

## Core Components

### 1. **SecretsManager** (index.js)
- **Purpose**: Main orchestrator, mirrors Python `MCPSecretsManager`
- **Dependencies**: FastMCP, existing `secrets_manager.js`
- **Key Methods**:
  - `initialize(serverName)`
  - `store_secret(name, value)`
  - `retrieve_secret(name)`
  - `ensure_secrets(secretNames)`

### 2. **Storage Layer** (storage.js)
- **Purpose**: Secure credential storage
- **Implementation**: Leverage existing `secrets_manager.js` which uses `@napi-rs/keyring`
- **Features**:
  - Cross-platform keychain/credential manager integration
  - Windows size limits (2560 bytes)
  - Index management for secret enumeration

### 3. **UI Handler** (ui-handler.js)
- **Purpose**: Cross-platform credential collection dialogs
- **Implementation Options**:
  - **Option A**: Port existing Rust binaries (copy from Python version)
  - **Option B**: Use Node.js native modules (like `node-notifier` + custom dialogs)
  - **Option C**: Web-based UI with local server (most portable)
- **Recommended**: Option A (reuse Rust binaries) for consistency

### 4. **Fetcher** (fetcher.js)
- **Purpose**: Async credential elicitation with FastMCP integration
- **Features**:
  - Verification code generation
  - FastMCP context integration (`ctx.info`, `ctx.elicit`)
  - Dialog spawning and result collection
  - Progress reporting

### 5. **Dialog Binaries** (secrets_dialog/)
- **Implementation**: Copy from Python version (already cross-platform)
- **Platforms**: macOS, Windows, Linux
- **Interface**: JSON stdin/stdout (same as Python)

## Technology Stack

### Core Dependencies
```json
{
  "fastmcp": "^latest",
  "@napi-rs/keyring": "^latest", 
  "zod": "^latest"
}
```

### Optional Dependencies
```json
{
  "crypto": "built-in",
  "child_process": "built-in", 
  "path": "built-in",
  "fs": "built-in"
}
```

## Implementation Plan

### Phase 1: Core Infrastructure
1. **Setup Package Structure**
   - `package.json` with FastMCP dependencies
   - TypeScript configuration
   - Basic module exports

2. **Storage Integration** 
   - Integrate existing `secrets_manager.js`
   - Add compatibility layer for Python API parity
   - Test cross-platform keychain access

### Phase 2: UI Integration
1. **Copy Dialog Binaries**
   - Copy Rust binaries from Python version
   - Test JSON interface compatibility
   - Create Node.js subprocess wrapper

2. **UI Handler Implementation**
   - Async dialog spawning
   - Error handling and cancellation
   - Platform-specific binary selection

### Phase 3: FastMCP Integration
1. **Fetcher Implementation**
   - FastMCP context integration
   - Verification code generation
   - Dialog coordination with MCP elicitation

2. **Main Manager Class**
   - API compatibility with Python version
   - FastMCP server integration
   - Session management

### Phase 4: Example Server
1. **Demo Server**
   - FastMCP server setup
   - Tool definitions requiring secrets
   - Authentication flow demonstration

## API Compatibility

The JavaScript implementation will maintain API compatibility with the Python version:

```javascript
// Main API (matches Python)
const { secrets_manager } = require('mcp-secrets-js');

// Initialize
secrets_manager.initialize('my-server');

// Storage operations
secrets_manager.store_secret('api_key', 'secret_value');
const value = secrets_manager.retrieve_secret('api_key');
const secrets = secrets_manager.list_secrets();

// Validation
const hasSecrets = secrets_manager.ensure_secrets(['api_key', 'endpoint']);

// FastMCP integration
const { fetch_secrets } = require('mcp-secrets-js/fetcher');
const success = await fetch_secrets(ctx, secretsInfo);
```

## File Structure
```
mcp-secrets-js/
├── package.json
├── tsconfig.json  
├── src/
│   ├── index.ts           # Main SecretsManager
│   ├── storage.ts         # Storage wrapper
│   ├── ui-handler.ts      # Dialog management
│   ├── fetcher.ts         # MCP integration
│   └── types.ts           # TypeScript definitions
├── secrets_dialog/        # Copied from Python
│   └── bin/
│       ├── macos_dialog
│       ├── linux_dialog
│       └── windows_dialog.exe
├── examples/
│   └── server.ts          # Demo FastMCP server
└── tests/
    └── *.test.ts
```

## Differences from Python Version

### Advantages
- **FastMCP Integration**: Native TypeScript MCP framework
- **Better Async**: Native Promise/async-await support
- **NPM Ecosystem**: Rich package ecosystem
- **Type Safety**: Full TypeScript support

### Considerations
- **Binary Distribution**: Need to bundle Rust binaries with NPM package
- **Platform Detection**: Node.js platform detection vs Python's `platform.system()`
- **Process Management**: Node.js `child_process` vs Python's `asyncio.subprocess`

## Security Considerations
- Maintain same security model as Python version
- Use `@napi-rs/keyring` for secure storage (already implemented)
- Inherit Rust dialog security properties
- Follow Node.js security best practices

## Testing Strategy
- Unit tests for each component
- Integration tests with FastMCP
- Cross-platform dialog testing
- Keychain integration verification
- Performance benchmarks vs Python version

## Deployment
- NPM package publication
- Binary inclusion strategy
- Platform-specific installation notes
- FastMCP integration examples
