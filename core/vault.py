"""
Windows Credential Manager integration for secure password storage
"""
import win32cred
from typing import Optional
import json


class VaultManager:
    """Manages secure credential storage using Windows Credential Manager"""
    
    TARGET_NAME_PREFIX = "StratupAutomation_"
    
    @staticmethod
    def store_credential(service: str, username: str, password: str) -> bool:
        """
        Store a credential in Windows Credential Manager.
        
        Args:
            service: Service name (e.g., "VPN", "browser_profile")
            username: Username associated with credential
            password: Password to store
            
        Returns:
            True if successful, False otherwise
        """
        target = f"{VaultManager.TARGET_NAME_PREFIX}{service}"
        
        try:
            cred = {
                "Type": 1,  # CRED_TYPE_GENERIC = 1
                "TargetName": target,
                "UserName": username,
                "CredentialBlob": password,
                "Persist": 2,  # CRED_PERSIST_LOCAL_MACHINE = 2
                "Comment": "Stratup Automation - VPN password"
            }
            
            # Write credential
            win32cred.CredWrite(cred, 0)
            return True
            
        except Exception as e:
            print(f"Failed to store credential for {service}: {e}")
            return False
    
    @staticmethod
    def get_credential(service: str) -> Optional[str]:
        """
        Retrieve a credential from Windows Credential Manager.
        
        Args:
            service: Service name to retrieve
            
        Returns:
            Password if found, None otherwise
        """
        target = f"{VaultManager.TARGET_NAME_PREFIX}{service}"
        
        try:
            cred = win32cred.CredRead(
                target,
                1,  # CRED_TYPE_GENERIC =1
                0
            )
            if cred and cred.get('CredentialBlob'):
                # CredentialBlob is bytes (UTF-16LE with null separators)
                blob = cred['CredentialBlob']
                if isinstance(blob, bytes):
                    # Decode UTF-16LE and strip nulls between characters
                    decoded = blob.decode('utf-16-le').rstrip('\x00')
                    return decoded
                return str(blob)
        except Exception:
            # Credential not found or error reading
            pass
        
        return None
    
    @staticmethod
    def delete_credential(service: str) -> bool:
        """
        Delete a credential from Windows Credential Manager.
        
        Args:
            service: Service name to delete
            
        Returns:
            True if successful, False otherwise
        """
        target = f"{VaultManager.TARGET_NAME_PREFIX}{service}"
        
        try:
            win32cred.CredDelete(target, 1, 0)  # CRED_TYPE_GENERIC = 1
            return True
        except Exception as e:
            print(f"Failed to delete credential for {service}: {e}")
            return False
    
    @staticmethod
    def list_credentials() -> list:
        """
        List all credentials stored for Stratup Automation.
        
        Returns:
            List of service names
        """
        services = []
        
        try:
            # Get all credentials
            creds = win32cred.CredEnumerate(None, 0)
            
            # Filter for our app
            for cred in creds:
                if cred['TargetName'].startswith(VaultManager.TARGET_NAME_PREFIX):
                    service = cred['TargetName'][len(VaultManager.TARGET_NAME_PREFIX):]
                    services.append(service)
                    
        except Exception as e:
            print(f"Failed to list credentials: {e}")
        
        return services


def get_vpn_password() -> Optional[str]:
    """
    Get VPN password from vault.
    
    Returns:
        Password if found, None otherwise
    """
    return VaultManager.get_credential("VPN")


def set_vpn_password(password: str) -> bool:
    """
    Set VPN password in vault.
    
    Args:
        password: Password to store
        
    Returns:
        True if successful, False otherwise
    """
    return VaultManager.store_credential("VPN", "user", password)


def delete_vpn_password() -> bool:
    """
    Delete VPN password from vault.
    
    Returns:
        True if successful, False otherwise
    """
    return VaultManager.delete_credential("VPN")
