# MCP Secrets: Technical Implementation Writeup

*A journey through the wasteland of credential management*

## The Mission

Build a secure secrets management framework for MCP servers that doesn't make you want to set your computer on fire.

The fundamental problem: MCP servers need credentials (API keys, passwords, tokens), but every obvious solution ranges from "slightly terrible" to "criminally negligent."

## The Journey

### Pre-Elicitation Era: The Dark Times

Before MCP elicitation existed (introduced June 2024), the landscape was bleak:

**Hidden files approach**: AWS-style dotfiles in user's home directory. Quick, easy, terrible. Works for AWS CLI because AWS I guess.

As someone who's written extensively on credential management, this felt wrong on multiple levels. Plain text secrets sitting in `~/.config/whatever` just waiting to be accidentally committed, backed up to cloud storage, or discovered by malware.

**Environment variable shimming**: Built prototypes that read from keychain but exposed key names through environment variables. Technically more secure than dotfiles, but still required manual pre-population. Fine for me, useless for anyone else.

The fundamental problem: no clean way to get credentials from users when needed.

### The Elicitation Promise

Then elicitation landed in the MCP spec (summer 2024). Looked perfect - direct input bypassing conversation logs, clean API integration. Built a working proof-of-concept.

Reality check: The spec explicitly warns against sensitive data in elicitations. Valid reasons:
- Developers consistently screw up secrets management  
- Opens attack vectors for phishing
- No guarantee MCP clients/utilities are trustworthy

Plus, with everyone setting tool use to auto-approve, phishing concerns are not theoretical.

### The Pivot: Out-of-Band + Keychain

Realized the actual answer was staring me in the face: **use the system keychain like a normal person.**

But simply storing in keychain wasn't enough - still needed user input for new credentials. The solution: out-of-band native dialogs.

1. **Detect missing secrets** → Check system keychain first
2. **Spawn native dialog** → OS-specific UI, not web nonsense  
3. **Use MCP elicitation** → But only to keep connection alive
4. **Collect credentials** → Through separate native dialog
5. **Store securely** → Commit to system keychain

### Security Through Paranoia

Added verification codes - random 8-character strings displayed in both the MCP client and the dialog. Prevents malicious software from creating fake credential-harvesting dialogs.

The dialog runs as a completely separate process, isolated from the MCP server. JSON template goes in via stdin, credentials come out via stdout. Clean, simple, auditable.

## Architecture Deep Dive

### Component Breakdown

```
┌─────────────────────┐
│ MCPSecretsManager   │ ← Main API, server-scoped operations
└──────────┬──────────┘
           │
┌─────────────────────┐
│ MCPSecretsStorage   │ ← Keychain abstraction layer  
└──────────┬──────────┘
           │
┌─────────────────────┐
│ System Keychain     │ ← Platform credential store
└─────────────────────┘

┌─────────────────────┐
│ fetch_secrets()     │ ← Orchestration function
└──────────┬──────────┘
           │
┌─────────────────────┐
│ AsyncUIHandler      │ ← Dialog process spawning
└──────────┬──────────┘
           │
┌─────────────────────┐
│ secrets_dialog      │ ← Rust native UI binaries
└─────────────────────┘
```

### Storage Layer

Uses platform-native credential stores:
- **macOS**: Keychain Services
- **Windows**: Credential Manager  
- **Linux**: libsecret/Secret Service

Each MCP server gets its own namespace (`com.mcp.{server-name}`). Secrets are isolated between servers. Maintains an index of stored secret names for enumeration.

Python uses the `keyring` library, JavaScript uses `@napi-rs/keyring`. Both provide the same underlying functionality with platform-specific backends.

### Dialog System

The UI is **not** a web interface. It's native OS dialogs compiled from Rust:
- **macOS**: Cocoa/AppKit native windows
- **Windows**: Win32 API native dialogs
- **Linux**: GTK3 native dialogs

Why Rust? Cross-compilation, single static binary per platform, no runtime dependencies. The dialog accepts a JSON template via stdin and outputs collected secrets via stdout. Clean process boundary.

Template structure:
```json
{
  "title": "MCP Secrets for MyServer",
  "description": "Verification Code: AB3F-9K2L\n\nConfirm this matches...",
  "fields": [
    {
      "name": "api_key",
      "label": "API Key", 
      "field_type": "password",
      "required": true,
      "help_text": "Your secret API key"
    }
  ]
}
```

Return codes:
- `0`: Success, secrets collected
- `1`: User cancelled 
- `2`: Error (invalid template, validation failure, etc.)

### Async Coordination

The tricky part: coordinating the dialog with MCP's elicitation system without blocking either.

The flow:
1. **Check existing secrets** → Fast keychain lookup
2. **Spawn dialog process** → Non-blocking, returns immediately
3. **Trigger MCP elicitation** → Keeps connection alive, shows verification code
4. **Wait for user action** → User clicks "Continue" in MCP client
5. **Await dialog completion** → Collect results from dialog process
6. **Store and continue** → Commit to keychain, return to MCP flow

This ensures the MCP connection doesn't timeout while the user fills out the dialog, and the dialog doesn't block the MCP server.

### Verification Codes

Generated as 8-character alphanumeric strings in `XXXX-XXXX` format. Displayed in both:
- The MCP elicitation message
- The native dialog window

User must verify the codes match before proceeding. Prevents:
- Random credential-harvesting dialogs
- Process injection attacks
- Social engineering via fake UIs

## Implementation Challenges

### Cross-Platform Keychain Access

Each platform has different credential storage APIs and limitations:

**Windows**: 2560-byte limit on credential values. Large secrets need chunking or compression, but honestly, what kinda secret are you storing if it's this big anyway?

**Linux**: Requires libsecret installation. Some distributions don't have it by default.

**macOS**: Most robust, but Keychain Access authorization can be finicky in sandboxed environments.

Abstracted these differences behind a common interface while preserving platform-specific optimizations.

### Process Management

Dialog spawning needs to work across platforms with different process models:

**Unix-like**: Standard fork/exec model, subprocess handles work well
**Windows**: Different process creation semantics, different signal handling

Used async subprocess spawning to avoid blocking the MCP server while dialogs run. Proper cleanup on cancellation to avoid zombie processes.

### MCP Framework Integration

Built for FastMCP (both Python and JavaScript versions), but kept the core secrets management separate from framework-specific code.

The `fetch_secrets()` function takes a "context" object that provides:
- `ctx.info()` - Logging/status messages  
- `ctx.elicit()` - MCP elicitation interface

This allows adaptation to other MCP frameworks by implementing the context interface.

### State Synchronization

The dialog runs independently of the MCP flow. Race conditions are possible:
- User closes dialog before clicking "Continue"
- User clicks "Continue" before dialog completes
- MCP client disconnects during dialog

Handled through proper async coordination and timeout mechanisms. The dialog process is cancelled if the MCP elicitation is cancelled.

## Security Model

### Threat Model

**In scope:**
- Credential theft by malicious software
- Accidental credential exposure in logs/processes
- UI spoofing attacks
- Cross-server credential leakage

**Out of scope:**
- OS-level compromise (if the OS is owned, you're screwed anyway)
- Physical access attacks
- Side-channel attacks on keychain implementations
- Network-based attacks (everything is local)

### Mitigations

**Keychain isolation**: Each server gets a unique namespace. Credentials can't leak between different MCP servers.

**Process isolation**: Dialog runs as separate process with minimal privileges. No access to MCP server memory space.

**UI verification**: Verification codes prevent fake dialogs from harvesting credentials.

**No network exposure**: Everything operates locally. No credentials transmitted over network.

**Minimal attack surface**: Dialog binary is small, single-purpose, auditable.

### Limitations

Still vulnerable to:
- Keyloggers (inherent to any keyboard input)
- Screen recording software  
- Malicious OS-level components
- Physical access to unlocked machine

But these are fundamental limitations of any credential input system.

## Language Implementations

### Python Version

Uses established libraries:
- `keyring` for cross-platform credential storage
- `asyncio` for process management
- `FastMCP` for MCP server framework

Straightforward implementation leveraging Python's mature ecosystem.

### JavaScript Version  

More complex due to ecosystem differences:
- `@napi-rs/keyring` for credential storage (Rust-based native module)
- Node.js `child_process` for dialog spawning
- FastMCP TypeScript framework

Required more careful handling of async operations and type safety.

Both implementations maintain API compatibility and share the same dialog binaries.

## Lessons Learned

### What Worked

**Native dialogs**: Users understand native OS dialogs. No confusion about what's asking for credentials.

**Verification codes**: Simple but effective anti-spoofing measure. Easy to verify, hard to fake.

**System keychain**: Leveraging existing OS security infrastructure instead of rolling our own.

**Process isolation**: Separate dialog process prevents credential contamination of MCP server.

### What Didn't

**Initial elicitation approach**: Seemed elegant but fundamentally flawed due to security concerns.

**Web-based UI**: Considered briefly, but native dialogs are more trustworthy and better UX.

**Embedded dialog**: Initially tried embedding dialog in MCP server process. Bad idea - harder to secure and audit.

### Design Decisions

**Why not environment variables?**: Visible in process lists, inherited by child processes, persist in shell history.

**Why not config files?**: Plain text on disk, easy to accidentally commit to git.

**Why not prompt in terminal?**: Visible to shoulder surfers, stored in shell history.

**Why not database?**: Adds complexity, still need to secure the database credentials.

**Why Rust for dialogs?**: Cross-compilation, static binaries, no runtime dependencies, small attack surface.

## Future Considerations

### Potential Improvements

**HSM integration**: For environments requiring hardware security modules.

**Credential rotation**: Automatic refresh of time-limited tokens.

**Audit logging**: Track credential access for compliance requirements.

**Backup/sync**: Securely synchronize credentials across machines.

**Remote MCP server support**: Current approach works for local servers. Remote MCP servers with API authentication present different challenges. One approach: create local MCP proxy servers that mount remote servers and inject authentication headers from keychain-stored credentials. This keeps API keys out of MCP configuration files while maintaining the same user experience.

### Scaling Challenges

Currently designed for single-user local development. Enterprise deployment would need:
- Central credential management
- Role-based access controls  
- Integration with existing identity systems
- Compliance with security policies

But that's a different problem with different requirements.

## Conclusion

What started as "just store some API keys" turned into a proper security engineering exercise. The final solution:

1. **Leverages OS security infrastructure** instead of inventing new crypto
2. **Provides clear security boundaries** between components  
3. **Maintains usability** through familiar native UI patterns
4. **Prevents common attack vectors** via verification codes and process isolation
5. **Works across platforms** without compromising security

The key insight: don't fight the platform security model, embrace it. Use the keychain, trust the OS, verify the user interface.

Is it perfect? No. Is it significantly better than the alternatives? Absolutely.

And that's good enough for now I suppose.
