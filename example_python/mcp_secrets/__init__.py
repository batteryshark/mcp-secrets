import os
from .storage import MCPSecretsStorage

class MCPSecretsManager:
    def __init__(self, server_name=None):
        self.secrets_storage = None
        self.session_permissions = {}  # In-memory cache for session permissions
        if server_name:
            self._initalize_manager(server_name)
            self.secrets_storage = MCPSecretsStorage(self.server_name)

    def initialize(self, server_name):
        self.server_name = server_name
        self.secrets_storage = MCPSecretsStorage(self.server_name)
        self.session_permissions = {}  # Reset permissions on initialization

    # Storage Stuff
    def store_secret(self, secret_name, secret_value):
        if not self.secrets_storage:
            raise Exception("Secrets storage not initialized")        
        self.secrets_storage.store_secret(secret_name, secret_value)

    def retrieve_secret(self, secret_name):
        if not self.secrets_storage:
            raise Exception("Secrets storage not initialized")        
        return self.secrets_storage.retrieve_secret(secret_name)
    
    def list_secrets(self):
        if not self.secrets_storage:
            raise Exception("Secrets storage not initialized")
        return self.secrets_storage.list_secrets()
    
    def clear_secrets(self):
        if not self.secrets_storage:
            raise Exception("Secrets storage not initialized")
        self.secrets_storage.clear_secrets()

    # API Stuff
    def ensure_secrets(self, secret_names):
        if not self.secrets_storage:
            raise Exception("Secrets storage not initialized")
        cached_secrets = self.list_secrets()
        # Compare the subsetlist of secrets with cached_secrets to see if all requested secrets are present
        return set(secret_names) <= set(cached_secrets)
    
    def secret_exists(self, secret_name):
        """Check if secret exists without retrieving its value."""
        if not self.secrets_storage:
            raise Exception("Secrets storage not initialized")
        return secret_name in self.list_secrets()
    
    async def retrieve_secret_with_permission(self, secret_name, ctx=None, reason=None):
        """Retrieve secret with permission check via elicitation."""
        if not self.secrets_storage:
            raise Exception("Secrets storage not initialized")
        
        # Check if secret exists
        if not self.secret_exists(secret_name):
            return None
        
        # Check for bypass environment variable
        bypass_prompts = os.getenv("MCP_BYPASS_SECRET_USE_CONFIRM", "false").lower() == "true"
        if bypass_prompts:
            return self.retrieve_secret(secret_name)
            
        # Check session permission cache
        if secret_name in self.session_permissions:
            return self.retrieve_secret(secret_name)
        
        # Need permission - require context for elicitation
        if not ctx:
            raise Exception("Context required for permission elicitation")
        
        # Build permission prompt
        prompt_message = f"{self.server_name} wants to use {secret_name}"
        if reason:
            prompt_message += f"\n\nReason: {reason}"
        
        # Elicit permission from user with multiple choice
        result = await ctx.elicit(
            message=prompt_message,
            response_type=["Allow", "Allow for Session", "Deny"]
        )
        
        if result.action != "accept" or not result.data:
            raise Exception(f"Permission denied for secret: {secret_name}")
        
        choice = result.data.strip()
        
        if choice == "Deny":
            raise Exception(f"Permission denied for secret: {secret_name}")
        elif choice == "Allow for Session":
            # Cache permission for this session
            self.session_permissions[secret_name] = True
        # "Allow" means just this once - no caching
        
        return self.retrieve_secret(secret_name)
    

       
# Global static instance - will be initialized in server.py
secrets_manager = MCPSecretsManager()
