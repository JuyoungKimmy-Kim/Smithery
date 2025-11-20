"""
Token Encryption Utility
Encrypts and decrypts MCP authentication tokens for secure storage
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class TokenEncryption:
    """
    Handles encryption and decryption of authentication tokens
    Uses Fernet (symmetric encryption) with a key derived from environment variable
    """

    @staticmethod
    def _get_encryption_key() -> bytes:
        """
        Get or generate encryption key from environment variable
        In production, this should be a strong secret stored securely
        """
        secret = os.getenv("TOKEN_ENCRYPTION_SECRET")

        if not secret:
            # For development, use a default (NOT for production!)
            logger.warning("TOKEN_ENCRYPTION_SECRET not set, using default (UNSAFE for production)")
            secret = "default-dev-secret-change-in-production"

        # Derive a proper key using PBKDF2
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"mcp-token-salt",  # In production, use a random salt stored separately
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
        return key

    @staticmethod
    def encrypt_token(token: str) -> str:
        """
        Encrypt a token for storage

        Args:
            token: Plain text token

        Returns:
            Encrypted token as base64 string
        """
        try:
            key = TokenEncryption._get_encryption_key()
            f = Fernet(key)
            encrypted = f.encrypt(token.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt token: {str(e)}")
            raise

    @staticmethod
    def decrypt_token(encrypted_token: str) -> str:
        """
        Decrypt a stored token

        Args:
            encrypted_token: Encrypted token as base64 string

        Returns:
            Plain text token
        """
        try:
            key = TokenEncryption._get_encryption_key()
            f = Fernet(key)
            decrypted = f.decrypt(encrypted_token.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt token: {str(e)}")
            raise

    @staticmethod
    def get_token_hint(token: str) -> str:
        """
        Get a hint for the token (last 4 characters)

        Args:
            token: Plain text token

        Returns:
            Last 4 characters or '****' if token is too short
        """
        if len(token) < 4:
            return "****"
        return f"...{token[-4:]}"
