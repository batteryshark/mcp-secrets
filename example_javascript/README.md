# MCP Secrets JS

A JavaScript/TypeScript implementation of secure credential management for MCP (Model Context Protocol) servers using FastMCP.

## Features

- 🔐 **Secure Storage**: Cross-platform credential storage using system keychain/credential manager
- 🖥️ **Native UI**: Cross-platform dialog boxes for credential collection  
- ⚡ **FastMCP Integration**: Built specifically for FastMCP framework
- 🔄 **API Compatibility**: Maintains compatibility with Python mcp_secrets
- 🛡️ **Type Safety**: Full TypeScript support with comprehensive type definitions

## Installation

```bash
npm install mcp-secrets-js
```

## Quick Start

```typescript
import { FastMCP } from 'fastmcp';
import { z } from 'zod';
import { secrets_manager, fetch_secrets } from 'mcp-secrets-js';

// Initialize secrets manager
secrets_manager.initialize('my-server');

// Define required secrets
const SECRETS_INFO = {
  api_key: {
    label: 'API Key',
    field_type: 'password',
    required: true,
    help_text: 'Your secret API key'
  }
};

// Create FastMCP server
const server = new FastMCP({
  name: 'My Server',
  version: '1.0.0'
});

// Add tool that requires secrets
server.addTool({
  name: 'protected_action',
  description: 'An action that requires API credentials',
  parameters: z.object({}),
  execute: async (args, context) => {
    // Check if secrets exist
    if (!secrets_manager.ensure_secrets(['api_key'])) {
      // Elicit secrets from user
      const [success, message] = await fetch_secrets(context, SECRETS_INFO);
      if (!success) {
        throw new Error(message);
      }
    }
    
    // Use the stored secret
    const apiKey = secrets_manager.retrieve_secret('api_key');
    return `Using API key: ${apiKey?.substring(0, 8)}...`;
  }
});

server.start({ transportType: 'stdio' });
```

## API Reference

### SecretsManager

```typescript
// Initialize with server name
secrets_manager.initialize('my-server');

// Store a secret
secrets_manager.store_secret('api_key', 'secret_value');

// Retrieve a secret
const value = secrets_manager.retrieve_secret('api_key');

// List all secret names
const names = secrets_manager.list_secrets();

// Check if all required secrets exist
const hasAll = secrets_manager.ensure_secrets(['api_key', 'token']);

// Clear all secrets
secrets_manager.clear_secrets();
```

### Secret Definitions

```typescript
interface SecretInfo {
  label: string;                                    // Display name
  field_type: 'text' | 'password' | 'url' | 'email';  // Input type
  required: boolean;                                // Whether required
  default?: string;                                 // Default value
  help_text?: string;                              // Help description
}
```

### Credential Elicitation

```typescript
import { fetch_secrets } from 'mcp-secrets-js';

const secretsConfig = {
  username: {
    label: 'Username',
    field_type: 'text',
    required: true
  },
  password: {
    label: 'Password', 
    field_type: 'password',
    required: true
  }
};

// Within a FastMCP tool
const [success, message] = await fetch_secrets(context, secretsConfig);
```

## Development

```bash
# Install dependencies
npm install

# Build the project
npm run build

# Run example server
npm run dev

# Inspect with MCP Inspector
npm run inspect

# Run tests
npm test
```

## Cross-Platform Support

This package includes native dialog binaries for:
- **macOS**: Native Cocoa dialogs
- **Windows**: Native Win32 dialogs  
- **Linux**: GTK-based dialogs

Binaries are automatically selected based on the runtime platform.

## Security

- Credentials are stored in the system's secure credential store (Keychain on macOS, Credential Manager on Windows, libsecret on Linux)
- No credentials are stored in plain text
- Dialog verification codes prevent UI spoofing attacks
- All operations respect platform security policies

## License

MIT

## Related Projects

- [FastMCP](https://github.com/punkpeye/fastmcp) - TypeScript MCP framework
- [mcp_secrets (Python)](https://github.com/original/mcp_secrets) - Original Python implementation
