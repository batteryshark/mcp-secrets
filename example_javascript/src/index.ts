import { MCPSecretsStorage } from './storage.js';

export class MCPSecretsManager {
  private secrets_storage: MCPSecretsStorage | null = null;
  private session_permissions: Map<string, boolean> = new Map(); // In-memory cache for session permissions
  public server_name: string | null = null;

  constructor(serverName?: string) {
    if (serverName) {
      this.initialize(serverName);
    }
  }

  initialize(serverName: string): void {
    this.server_name = serverName;
    this.secrets_storage = new MCPSecretsStorage(serverName);
    this.session_permissions.clear(); // Reset permissions on initialization
  }

  // Storage operations
  store_secret(secretName: string, secretValue: string): void {
    if (!this.secrets_storage) {
      throw new Error('Secrets storage not initialized');
    }
    this.secrets_storage.store_secret(secretName, secretValue);
  }

  retrieve_secret(secretName: string): string | null {
    if (!this.secrets_storage) {
      throw new Error('Secrets storage not initialized');
    }
    return this.secrets_storage.retrieve_secret(secretName);
  }

  list_secrets(): string[] {
    if (!this.secrets_storage) {
      throw new Error('Secrets storage not initialized');
    }
    return this.secrets_storage.list_secrets();
  }

  clear_secrets(): void {
    if (!this.secrets_storage) {
      throw new Error('Secrets storage not initialized');
    }
    this.secrets_storage.clear_secrets();
  }

  // API validation
  ensure_secrets(secretNames: string[]): boolean {
    if (!this.secrets_storage) {
      throw new Error('Secrets storage not initialized');
    }
    const cachedSecrets = this.list_secrets();
    const secretSet = new Set(secretNames);
    const cachedSet = new Set(cachedSecrets);
    
    // Check if all requested secrets are present
    return secretNames.every(name => cachedSet.has(name));
  }

  secret_exists(secretName: string): boolean {
    if (!this.secrets_storage) {
      throw new Error('Secrets storage not initialized');
    }
    return this.list_secrets().includes(secretName);
  }

  async retrieve_secret_with_permission(
    secretName: string, 
    ctx?: any, 
    reason?: string
  ): Promise<string | null> {
    if (!this.secrets_storage) {
      throw new Error('Secrets storage not initialized');
    }

    // Check if secret exists
    if (!this.secret_exists(secretName)) {
      return null;
    }

    // Check for bypass environment variable
    const bypassPrompts = process.env.MCP_BYPASS_SECRET_USE_CONFIRM?.toLowerCase() === 'true';
    if (bypassPrompts) {
      return this.retrieve_secret(secretName);
    }

    // Check session permission cache
    if (this.session_permissions.has(secretName)) {
      return this.retrieve_secret(secretName);
    }

    // Need permission - require context for elicitation
    if (!ctx) {
      throw new Error('Context required for permission elicitation');
    }

    // Build permission prompt
    let promptMessage = `${this.server_name} wants to use ${secretName}`;
    if (reason) {
      promptMessage += `\n\nReason: ${reason}`;
    }

    // Elicit permission from user with multiple choice
    const result = await ctx.elicit(promptMessage, ['Allow', 'Allow for Session', 'Deny']);

    if (result.action !== 'accept' || !result.data) {
      throw new Error(`Permission denied for secret: ${secretName}`);
    }

    const choice = result.data.trim();

    if (choice === 'Deny') {
      throw new Error(`Permission denied for secret: ${secretName}`);
    } else if (choice === 'Allow for Session') {
      // Cache permission for this session
      this.session_permissions.set(secretName, true);
    }
    // "Allow" means just this once - no caching

    return this.retrieve_secret(secretName);
  }
}

// Global static instance - will be initialized in server
export const secrets_manager = new MCPSecretsManager();

// Re-export other components
export { fetch_secrets } from './fetcher.js';
export { AsyncUIHandler, get_async_ui_handler } from './ui-handler.js';
export { MCPSecretsStorage } from './storage.js';
export * from './types.js';
