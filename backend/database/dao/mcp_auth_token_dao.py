"""
Data Access Object for MCP Auth Tokens
"""

from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from backend.database.model.mcp_auth_token import MCPAuthToken
from backend.utils.token_encryption import TokenEncryption

logger = logging.getLogger(__name__)


class MCPAuthTokenDAO:
    """DAO for managing MCP authentication tokens"""

    def __init__(self, db: Session):
        self.db = db

    def save_token(self, user_id: int, mcp_server_id: int, token: str) -> MCPAuthToken:
        """
        Save or update authentication token for a user and MCP server

        Args:
            user_id: User ID
            mcp_server_id: MCP Server ID
            token: Plain text token

        Returns:
            MCPAuthToken object
        """
        try:
            # Check if token already exists
            existing = self.db.query(MCPAuthToken).filter(
                MCPAuthToken.user_id == user_id,
                MCPAuthToken.mcp_server_id == mcp_server_id
            ).first()

            # Encrypt token
            encrypted_token = TokenEncryption.encrypt_token(token)
            token_hint = TokenEncryption.get_token_hint(token)

            if existing:
                # Update existing token
                existing.token_encrypted = encrypted_token
                existing.token_hint = token_hint
                existing.updated_at = datetime.utcnow()
                logger.info(f"Updated auth token for user {user_id}, server {mcp_server_id}")
            else:
                # Create new token
                existing = MCPAuthToken(
                    user_id=user_id,
                    mcp_server_id=mcp_server_id,
                    token_encrypted=encrypted_token,
                    token_hint=token_hint
                )
                self.db.add(existing)
                logger.info(f"Created auth token for user {user_id}, server {mcp_server_id}")

            self.db.commit()
            self.db.refresh(existing)
            return existing

        except Exception as e:
            logger.error(f"Failed to save token: {str(e)}")
            self.db.rollback()
            raise

    def get_token(self, user_id: int, mcp_server_id: int) -> Optional[str]:
        """
        Get decrypted authentication token for a user and MCP server

        Args:
            user_id: User ID
            mcp_server_id: MCP Server ID

        Returns:
            Plain text token or None if not found
        """
        try:
            token_record = self.db.query(MCPAuthToken).filter(
                MCPAuthToken.user_id == user_id,
                MCPAuthToken.mcp_server_id == mcp_server_id
            ).first()

            if not token_record:
                return None

            # Update last used timestamp
            token_record.last_used_at = datetime.utcnow()
            self.db.commit()

            # Decrypt and return token
            return TokenEncryption.decrypt_token(token_record.token_encrypted)

        except Exception as e:
            logger.error(f"Failed to get token: {str(e)}")
            return None

    def delete_token(self, user_id: int, mcp_server_id: int) -> bool:
        """
        Delete authentication token for a user and MCP server

        Args:
            user_id: User ID
            mcp_server_id: MCP Server ID

        Returns:
            True if deleted, False if not found
        """
        try:
            token_record = self.db.query(MCPAuthToken).filter(
                MCPAuthToken.user_id == user_id,
                MCPAuthToken.mcp_server_id == mcp_server_id
            ).first()

            if not token_record:
                return False

            self.db.delete(token_record)
            self.db.commit()
            logger.info(f"Deleted auth token for user {user_id}, server {mcp_server_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete token: {str(e)}")
            self.db.rollback()
            return False

    def get_user_tokens(self, user_id: int):
        """
        Get all tokens for a user (without decrypting)

        Args:
            user_id: User ID

        Returns:
            List of MCPAuthToken objects
        """
        return self.db.query(MCPAuthToken).filter(
            MCPAuthToken.user_id == user_id
        ).all()
