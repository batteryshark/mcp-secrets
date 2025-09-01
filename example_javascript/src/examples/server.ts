import { FastMCP } from 'fastmcp';
import { z } from 'zod';
import { secrets_manager, fetch_secrets } from '../index.js';
import type { SecretInfo } from '../types.js';

// Server-specific secrets configuration
const SECRETS_INFO: Record<string, SecretInfo> = {
  api_key: {
    label: 'API Key',
    field_type: 'password',
    required: true,
    help_text: 'Your secret API key from the service dashboard'
  },
  endpoint: {
    label: 'API Endpoint', 
    field_type: 'url',
    default: 'https://api.example.com',
    required: true,
    help_text: 'The base URL for API requests'
  },
  timeout: {
    label: 'Request Timeout (seconds)',
    field_type: 'text',
    default: '30',
    required: false,
    help_text: 'How long to wait for API responses'
  }
};

// Initialize FastMCP server
const server = new FastMCP({
  name: 'MCP Secrets Example JS',
  version: '1.0.0',
  instructions: `
    Reference implementation for MCP servers using secrets management in JavaScript.

    This server demonstrates best practices for:
    - Secure credential storage and retrieval using FastMCP
    - Interactive credential elicitation 
    - Authentication middleware
    - Modular tool organization

    Use some_tool_that_needs_secrets to test the credential flow,
    and clear_secrets to reset stored credentials.
  `
});

// Initialize secrets manager for this server
secrets_manager.initialize('MCP Secrets Example JS');

// Register tools
server.addTool({
  name: 'some_tool_that_needs_secrets',
  description: 'This tool demonstrates credential handling and will elicit secrets if needed',
  parameters: z.object({}),
  execute: async (args, { log }) => {
    const allSecretsPresent = secrets_manager.ensure_secrets(['api_key', 'endpoint', 'timeout']);
    
    if (allSecretsPresent) {
      await log.info('All secrets present');
      
      // Demonstrate access to stored secrets
      const apiKey = secrets_manager.retrieve_secret('api_key');
      const endpoint = secrets_manager.retrieve_secret('endpoint');
      const timeout = secrets_manager.retrieve_secret('timeout');
      
      return `✅ Secrets available!\nEndpoint: ${endpoint}\nTimeout: ${timeout}s\nAPI Key: ${apiKey?.substring(0, 8)}...`;
    } else {
      await log.info('Some secrets are missing');
      
      // This would need to be adapted for FastMCP context
      // The Python version uses a custom Context type
      const mockContext = {
        info: async (msg: string) => {
          await log.info(msg);
        },
        elicit: async (options: any) => {
          // In a real implementation, this would use FastMCP's sampling feature
          // For now, we'll simulate user acceptance
          return { action: 'accept' };
        }
      };
      
      const [status, message] = await fetch_secrets(mockContext, SECRETS_INFO);
      
      if (!status) {
        throw new Error(message);
      }
      
      await log.info(message);
      return 'Secrets Tool OK!';
    }
  }
});

server.addTool({
  name: 'clear_secrets',
  description: 'Reset the secrets manager and clear all stored credentials',
  parameters: z.object({}),
  execute: async () => {
    secrets_manager.clear_secrets();
    return '🗑️ All secrets cleared!';
  }
});

server.addTool({
  name: 'list_secrets',
  description: 'List all currently stored secret names (for debugging)',
  parameters: z.object({}),
  execute: async () => {
    const secretNames = secrets_manager.list_secrets();
    if (secretNames.length === 0) {
      return '📝 No secrets currently stored';
    }
    return `📝 Stored secrets: ${secretNames.join(', ')}`;
  }
});

// Start the server
server.start({
  transportType: 'stdio'
});

export default server;
