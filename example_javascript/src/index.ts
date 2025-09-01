import { MCPSecretsStorage } from './storage.js';

export class MCPSecretsManager {
  private secrets_storage: MCPSecretsStorage | null = null;
  public server_name: string | null = null;

  constructor(serverName?: string) {
    if (serverName) {
      this.initialize(serverName);
    }
  }

  initialize(serverName: string): void {
    this.server_name = serverName;
    this.secrets_storage = new MCPSecretsStorage(serverName);
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
}

// Global static instance - will be initialized in server
export const secrets_manager = new MCPSecretsManager();

// Re-export other components
export { fetch_secrets } from './fetcher.js';
export { AsyncUIHandler, get_async_ui_handler } from './ui-handler.js';
export { MCPSecretsStorage } from './storage.js';
export * from './types.js';
