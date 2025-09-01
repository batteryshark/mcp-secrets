// Storage implementation using @napi-rs/keyring
import { Entry } from '@napi-rs/keyring';

const INDEX_USERNAME = '__secret_index__';

export class MCPSecretsStorage {
  private serviceName: string;

  constructor(serverName: string) {
    this.serviceName = `com.mcp.${serverName}`;
    
    // Check for clear flag
    if (process.env.SECRETS_STORAGE_CLEAR === 'true') {
      this._deleteAllSecrets();
      console.log('SECRETS_STORAGE_CLEAR is set, cleared all secrets');
    }
  }

  private _serializeSecretContent(content: string): string {
    return String(content);
  }

  private _deserializeSecretContent(serialized: string): string {
    return serialized;
  }

  private _serializeIndexContent(indexSet: Set<string>): string {
    return JSON.stringify(Array.from(indexSet));
  }

  private _deserializeIndexContent(serializedIndex: string | null): Set<string> {
    if (!serializedIndex) return new Set();
    try {
      const parsed = JSON.parse(serializedIndex);
      return Array.isArray(parsed) ? new Set(parsed) : new Set();
    } catch {
      return new Set();
    }
  }

  private _getSecretIndex(): Set<string> {
    try {
      const raw = new Entry(this.serviceName, INDEX_USERNAME).getPassword();
      return this._deserializeIndexContent(raw);
    } catch {
      return new Set();
    }
  }

  private _setSecretIndex(indexSet: Set<string>): void {
    const payload = this._serializeIndexContent(indexSet);
    new Entry(this.serviceName, INDEX_USERNAME).setPassword(payload);
  }

  private _updateSecretIndex(secretName: string): void {
    const idx = this._getSecretIndex();
    idx.add(secretName);
    this._setSecretIndex(idx);
  }

  private _removeFromSecretIndex(secretName: string): void {
    const idx = this._getSecretIndex();
    idx.delete(secretName);
    if (idx.size > 0) {
      this._setSecretIndex(idx);
    } else {
      try {
        new Entry(this.serviceName, INDEX_USERNAME).deletePassword();
      } catch {
        // ignore if it doesn't exist
      }
    }
  }

  private _deleteAllSecrets(): void {
    const idx = this._getSecretIndex();
    for (const name of idx) {
      try {
        new Entry(this.serviceName, name).deletePassword();
      } catch {
        // ignore missing
      }
    }
    try {
      new Entry(this.serviceName, INDEX_USERNAME).deletePassword();
    } catch {
      // ignore missing
    }
  }

  store_secret(secretName: string, content: string): void {
    const serialized = this._serializeSecretContent(content);
    new Entry(this.serviceName, secretName).setPassword(serialized);
    this._updateSecretIndex(secretName);
  }

  retrieve_secret(secretName: string): string | null {
    try {
      const raw = new Entry(this.serviceName, secretName).getPassword();
      return raw ? this._deserializeSecretContent(raw) : null;
    } catch {
      return null;
    }
  }

  delete_secret(secretName: string): void {
    try {
      new Entry(this.serviceName, secretName).deletePassword();
      this._removeFromSecretIndex(secretName);
    } catch {
      // ignore if it doesn't exist
    }
  }

  list_secrets(): string[] {
    const idx = this._getSecretIndex();
    return Array.from(idx);
  }

  clear_secrets(): void {
    this._deleteAllSecrets();
  }
}
