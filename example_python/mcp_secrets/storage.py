import os 
import json
import keyring
import logging

# Note: Linux needs libsecret to use this.
# Note2: Windows has a limit of 2560 characters for the password.
# Note3: clear secrets on init with SECRETS_STORAGE_CLEAR=true

class MCPSecretsStorage:
    """MCP Secrets Storage for secure keyring-based secret storage."""

    def __init__(self, server_name):
        """Initialize the secrets storage for a specific MCP server.

        Args:
            server_name: The name of the MCP server (e.g., 'findmy-server', 'google-maps-server')
        """
        self.service_name = f"com.mcp.{server_name}"
        if os.getenv("SECRETS_STORAGE_CLEAR", "false") == "true":
            self._delete_all_secrets()
            logging.info("SECRETS_STORAGE_CLEAR is set, cleared all secrets")
            
    def _serialize_secret_content(self, content):
        """Serialize secret content - always convert to string"""
        return str(content)

    def _deserialize_secret_content(self, serialized_content):
        """Deserialize secret content - return as stored string"""
        return serialized_content

    def _serialize_index_content(self, index_set):
        """Serialize index set as JSON list"""
        return json.dumps(list(index_set))

    def _deserialize_index_content(self, serialized_index):
        """Deserialize index from JSON list to set"""
        if serialized_index:
            try:
                data = json.loads(serialized_index)
                return set(data) if isinstance(data, list) else set()
            except json.JSONDecodeError:
                return set()
        return set()

    def _get_secret_index(self):
        """Get the index of all secrets for this server"""
        index_username = "__secret_index__"
        index_data = keyring.get_password(self.service_name, index_username)
        return self._deserialize_index_content(index_data)

    def _update_secret_index(self, secret_name):
        """Update the index to include a new secret"""
        index = self._get_secret_index()
        index.add(secret_name)  # Add to set
        index_username = "__secret_index__"
        keyring.set_password(self.service_name, index_username, self._serialize_index_content(index))

    def _remove_from_secret_index(self, secret_name):
        """Remove a secret from the index"""
        index = self._get_secret_index()
        index.discard(secret_name)  # Remove from set (safe if not present)
        if index:  # If there are still secrets, update the index
            index_username = "__secret_index__"
            keyring.set_password(self.service_name, index_username, self._serialize_index_content(index))
        else:  # If no secrets left, remove the index entirely
            index_username = "__secret_index__"
            try:
                keyring.delete_password(self.service_name, index_username)
            except Exception:
                pass  # Index might not exist, that's fine
        
    def _delete_all_secrets(self):
        """Delete all secrets for this server"""
        index = self._get_secret_index()
        for secret_name in index:
            self.delete_secret(secret_name)
        # Finally, delete the index
        try:
            keyring.delete_password(self.service_name, "__secret_index__")
        except Exception:
            pass  # Index might not exist, that's fine

    def store_secret(self, secret_name, content):
        """Store a secret in the keyring for this server.

        Args:
            secret_name: Name of the secret
            content: The secret content (string, dict, or list)
        """
        username = secret_name
        # Serialize content for storage (with JSON prefix for complex types)
        serialized_content = self._serialize_secret_content(content)
        # Store the content in the keychain
        keyring.set_password(self.service_name, username, serialized_content)
        # Update the index of secrets for this server
        self._update_secret_index(secret_name)

    def retrieve_secret(self, secret_name):
        """Retrieve a secret from the keyring for this server.

        Args:
            secret_name: Name of the secret to retrieve

        Returns:
            The secret content, or None if not found
        """
        username = secret_name
        # Retrieve the content from the keychain
        serialized_content = keyring.get_password(self.service_name, username)
        return self._deserialize_secret_content(serialized_content)

    def delete_secret(self, secret_name):
        """Delete a secret from the keyring for this server.

        Args:
            secret_name: Name of the secret to delete
        """
        username = secret_name
        keyring.delete_password(self.service_name, username)
        # Remove from the index
        self._remove_from_secret_index(secret_name)

    def list_secrets(self):
        """List all secret names for this server.

        Returns:
            List of secret names
        """
        index = self._get_secret_index()
        return list(index) if index else []

    def clear_secrets(self):
        """Clear all secrets for this server"""
        self._delete_all_secrets()


