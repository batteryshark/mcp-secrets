import { get_async_ui_handler } from './ui-handler.js';
import { secrets_manager } from './index.js';
import type { MCPContext, SecretInfo, SecretsTemplate } from './types.js';

export async function fetch_secrets(
  ctx: MCPContext, 
  secrets_info: Record<string, SecretInfo>
): Promise<[boolean, string]> {
  // Prepare fields without showing existing secret values for security
  const fields: SecretInfo[] = [];
  
  for (const [fieldName, fieldInfo] of Object.entries(secrets_info)) {
    const fieldWithName = { ...fieldInfo, name: fieldName };
    // Don't pre-populate with existing values for security reasons
    fields.push(fieldWithName);
  }

  const verificationCode = generate_verification_code();
  const template: SecretsTemplate = {
    title: `MCP Secrets for ${secrets_manager.server_name}`,
    description: `Verification Code: ${verificationCode}\n\nConfirm this code matches what's displayed in your MCP host before proceeding.`,
    fields
  };

  // Spawn dialog FIRST (non-blocking)
  const uiHandler = get_async_ui_handler();
  const dialogPromise = uiHandler.collect_secrets_async(template);
  
  await ctx.info(JSON.stringify(template));
  
  // THEN do MCP elicitation (keeps connection alive)
  await ctx.info('🔑 A credential dialog should appear. Fill it out, then click \'Continue\' below.');
  
  const result = await ctx.elicit({
    message: `Secrets Requested [Code: ${verificationCode}] - Click 'Continue' when finished`,
    response_type: null
  });
  
  if (result.action !== 'accept') {
    return [false, '❌ Secrets fetch cancelled by user.'];
  }
  
  // Now await the dialog results
  let secrets;
  try {
    secrets = await dialogPromise;
  } catch (error) {
    return [false, `❌ Dialog error: ${error instanceof Error ? error.message : String(error)}`];
  }
  
  if (!secrets) {
    return [false, '❌ Dialog was cancelled by user.'];
  }
  
  // Store the secrets (only update if new value provided)
  let storedCount = 0;
  for (const [fieldName, value] of Object.entries(secrets)) {
    if (value) { // Only update secrets with new non-empty values
      secrets_manager.store_secret(fieldName, value);
      storedCount++;
    }
  }
  
  return [true, `✅ Successfully stored ${storedCount} credentials.`];
}

function generate_verification_code(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  const part1 = Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
  const part2 = Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
  return `${part1}-${part2}`;
}
