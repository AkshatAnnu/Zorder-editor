#!/usr/bin/env python3
"""
Secure credential storage for Zorder Agent using dual-key encryption
"""
import os
import keyring
from cryptography.fernet import Fernet
import json
import logging

logger = logging.getLogger(__name__)

# Key identifiers for Windows Credential Manager
USERNAME_KEY_ID = "zorder_fernet_key_u"
PASSWORD_KEY_ID = "zorder_fernet_key_p"
KEYRING_SERVICE = "ZorderAgent"

# Default credentials file path
DEFAULT_CREDS_PATH = os.path.join(os.getenv("APPDATA", ""), "Zorder", "creds.bin")

class SecretStore:
    """Secure storage for username/password using dual-key encryption."""
    
    def __init__(self, creds_path=None):
        self.creds_path = creds_path or DEFAULT_CREDS_PATH
        self.username_key = None
        self.password_key = None
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.creds_path), exist_ok=True)
    
    def _get_or_create_key(self, key_id):
        """Get encryption key from Windows Credential Manager or create new one."""
        try:
            # Try to retrieve existing key
            key_b64 = keyring.get_password(KEYRING_SERVICE, key_id)
            if key_b64:
                return key_b64.encode()
            
            # Create new key if not found
            key = Fernet.generate_key()
            keyring.set_password(KEYRING_SERVICE, key_id, key.decode())
            logger.info(f"Created new encryption key: {key_id}")
            return key
            
        except Exception as e:
            logger.error(f"Failed to get/create key {key_id}: {e}")
            raise RuntimeError(f"Key management failed: {e}")
    
    def _get_username_key(self):
        """Get username encryption key."""
        if not self.username_key:
            self.username_key = self._get_or_create_key(USERNAME_KEY_ID)
        return self.username_key
    
    def _get_password_key(self):
        """Get password encryption key."""
        if not self.password_key:
            self.password_key = self._get_or_create_key(PASSWORD_KEY_ID)
        return self.password_key
    
    def save_credentials(self, username, password):
        """
        Encrypt and save username/password using separate keys.
        
        Args:
            username (str): Username to encrypt and save
            password (str): Password to encrypt and save
        """
        try:
            # Get encryption keys
            username_key = self._get_username_key()
            password_key = self._get_password_key()
            
            # Create Fernet ciphers
            username_cipher = Fernet(username_key)
            password_cipher = Fernet(password_key)
            
            # Encrypt credentials
            encrypted_username = username_cipher.encrypt(username.encode())
            encrypted_password = password_cipher.encrypt(password.encode())
            
            # Create data structure
            creds_data = {
                "username": encrypted_username.decode(),
                "password": encrypted_password.decode(),
                "version": "1.0"
            }
            
            # Save to file
            with open(self.creds_path, 'w') as f:
                json.dump(creds_data, f, indent=2)
            
            # Set restrictive permissions on Windows (owner only)
            try:
                import stat
                os.chmod(self.creds_path, stat.S_IREAD | stat.S_IWRITE)
            except:
                pass  # Windows permissions handled differently
            
            logger.info("Credentials saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            raise RuntimeError(f"Credential save failed: {e}")
    
    def load_credentials(self):
        """
        Load and decrypt username/password.
        
        Returns:
            tuple: (username, password) or (None, None) if not found
        """
        try:
            # Check if credentials file exists
            if not os.path.exists(self.creds_path):
                logger.info("No credentials file found")
                return None, None
            
            # Load encrypted data
            with open(self.creds_path, 'r') as f:
                creds_data = json.load(f)
            
            # Get decryption keys
            username_key = self._get_username_key()
            password_key = self._get_password_key()
            
            # Create Fernet ciphers
            username_cipher = Fernet(username_key)
            password_cipher = Fernet(password_key)
            
            # Decrypt credentials
            encrypted_username = creds_data["username"].encode()
            encrypted_password = creds_data["password"].encode()
            
            username = username_cipher.decrypt(encrypted_username).decode()
            password = password_cipher.decrypt(encrypted_password).decode()
            
            logger.info("Credentials loaded successfully")
            return username, password
            
        except FileNotFoundError:
            logger.info("Credentials file not found")
            return None, None
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            raise RuntimeError(f"Credential load failed: {e}")
    
    def delete_credentials(self):
        """Delete stored credentials and encryption keys."""
        try:
            # Delete credentials file
            if os.path.exists(self.creds_path):
                os.remove(self.creds_path)
                logger.info("Credentials file deleted")
            
            # Delete keys from Windows Credential Manager
            try:
                keyring.delete_password(KEYRING_SERVICE, USERNAME_KEY_ID)
            except:
                pass
            
            try:
                keyring.delete_password(KEYRING_SERVICE, PASSWORD_KEY_ID)
            except:
                pass
            
            logger.info("Credentials deleted successfully")
            
        except Exception as e:
            logger.error(f"Failed to delete credentials: {e}")
            raise RuntimeError(f"Credential deletion failed: {e}")
    
    def has_credentials(self):
        """Check if credentials are stored."""
        return os.path.exists(self.creds_path)

# Convenience functions for backward compatibility
_default_store = None

def get_default_store():
    """Get the default secret store instance."""
    global _default_store
    if not _default_store:
        _default_store = SecretStore()
    return _default_store

def save_credentials(username, password):
    """Save credentials using default store."""
    store = get_default_store()
    store.save_credentials(username, password)

def load_credentials():
    """Load credentials using default store."""
    store = get_default_store()
    return store.load_credentials()

def delete_credentials():
    """Delete credentials using default store."""
    store = get_default_store()
    store.delete_credentials()

def has_credentials():
    """Check if credentials exist using default store."""
    store = get_default_store()
    return store.has_credentials()

if __name__ == "__main__":
    """Test/setup script for credentials."""
    import getpass
    
    print("Zorder Agent - Credential Setup")
    print("=" * 40)
    
    store = SecretStore()
    
    if store.has_credentials():
        print("Existing credentials found.")
        choice = input("Do you want to (v)iew, (u)pdate, or (d)elete them? [v/u/d]: ").lower()
        
        if choice == 'v':
            try:
                username, password = store.load_credentials()
                print(f"Username: {username}")
                print(f"Password: {'*' * len(password) if password else 'None'}")
            except Exception as e:
                print(f"Error loading credentials: {e}")
        
        elif choice == 'u':
            username = input("Enter new username: ")
            password = getpass.getpass("Enter new password: ")
            
            try:
                store.save_credentials(username, password)
                print("Credentials updated successfully!")
            except Exception as e:
                print(f"Error saving credentials: {e}")
        
        elif choice == 'd':
            confirm = input("Are you sure you want to delete credentials? [y/N]: ").lower()
            if confirm == 'y':
                try:
                    store.delete_credentials()
                    print("Credentials deleted successfully!")
                except Exception as e:
                    print(f"Error deleting credentials: {e}")
    
    else:
        print("No credentials found. Setting up new credentials...")
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
        
        try:
            store.save_credentials(username, password)
            print("Credentials saved successfully!")
        except Exception as e:
            print(f"Error saving credentials: {e}")


