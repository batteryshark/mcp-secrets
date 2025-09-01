import { spawn } from 'child_process';
import { platform } from 'os';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import type { SecretsTemplate, DialogResult } from './types.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export class AsyncUIHandler {
  private handlerBinary: string;

  constructor(handlerBinary?: string) {
    this.handlerBinary = handlerBinary || this.getDefaultBinary();
  }

  private getDefaultBinary(): string {
    const basePath = join(__dirname, '..', 'dialog_bin');
    
    const platformName = platform();
    if (platformName === 'darwin') {
      return join(basePath, 'macos_dialog');
    } else if (platformName === 'win32') {
      return join(basePath, 'windows_dialog.exe');
    } else {
      return join(basePath, 'linux_dialog');
    }
  }

  async collect_secrets_async(template: SecretsTemplate): Promise<DialogResult | null> {
    return new Promise((resolve, reject) => {
      const process = spawn(this.handlerBinary, [], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      process.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      process.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      process.on('close', (code) => {
        if (code === 1) {
          resolve(null); // User cancelled
        } else if (code !== 0) {
          const errorMsg = stderr.trim() || 'Unknown error';
          reject(new Error(`UI dialog failed: ${errorMsg}`));
        } else {
          try {
            const result = JSON.parse(stdout);
            resolve(result);
          } catch (e) {
            reject(new Error(`Invalid JSON from dialog: ${e}`));
          }
        }
      });

      process.on('error', (err) => {
        if (err.message.includes('ENOENT')) {
          reject(new Error(`Dialog binary not found: ${this.handlerBinary}`));
        } else {
          reject(new Error(`Dialog error: ${err.message}`));
        }
      });

      // Send template to dialog
      process.stdin.write(JSON.stringify(template));
      process.stdin.end();
    });
  }
}

export function get_async_ui_handler(): AsyncUIHandler {
  // Check for custom binary path
  const customBinary = process.env.MCP_SECRETS_UI_BINARY;
  
  if (customBinary) {
    return new AsyncUIHandler(customBinary);
  }
  
  return new AsyncUIHandler();
}
