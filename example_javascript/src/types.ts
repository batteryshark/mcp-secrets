// Type definitions for MCP Secrets JS

export interface SecretInfo {
  label: string;
  field_type: 'text' | 'password' | 'url' | 'email';
  required: boolean;
  default?: string;
  help_text?: string;
  name?: string;
  value?: string;
}

export interface SecretsTemplate {
  title: string;
  description: string;
  fields: SecretInfo[];
}

export interface DialogResult {
  [key: string]: string;
}

export interface MCPContext {
  info: (message: string) => Promise<void>;
  elicit: (options: { message: string; response_type?: any }) => Promise<{ action: string }>;
}

export interface SessionData {
  [key: string]: unknown;
}
