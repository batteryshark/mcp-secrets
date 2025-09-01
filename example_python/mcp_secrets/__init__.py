from .storage import MCPSecretsStorage

class MCPSecretsManager:
    def __init__(self, server_name=None):
        self.secrets_storage = None
        if server_name:
            self._initalize_manager(server_name)
            self.secrets_storage = MCPSecretsStorage(self.server_name)

    def initialize(self, server_name):
        self.server_name = server_name
        self.secrets_storage = MCPSecretsStorage(self.server_name)

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
    

       
# Global static instance - will be initialized in server.py
secrets_manager = MCPSecretsManager()
