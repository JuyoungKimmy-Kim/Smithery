from sqlalchemy.orm import Session
from typing import Optional, List
from backend.database.dao.notification_dao import NotificationDAO
from backend.database.dao.user_dao import UserDAO
from backend.database.dao.mcp_server_dao import MCPServerDAO
from backend.database.model.notification import Notification
from backend.database.model.user import User

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_dao = NotificationDAO(db)
        self.user_dao = UserDAO(db)
        self.mcp_dao = MCPServerDAO(db)

    def create_comment_notification(
        self,
        mcp_server_id: int,
        commenter_user_id: int
    ) -> Optional[Notification]:
        """댓글 알림을 생성합니다."""
        # MCP 서버 정보 조회
        mcp_server = self.mcp_dao.get_mcp_server_by_id(mcp_server_id)
        if not mcp_server:
            return None

        # MCP 소유자 ID
        owner_id = mcp_server.owner_id

        # 자기 자신의 댓글은 알림 생성하지 않음
        if owner_id == commenter_user_id:
            return None

        # 댓글 작성자 정보 조회
        commenter = self.user_dao.get_user_by_id(commenter_user_id)
        if not commenter:
            return None

        # 알림 메시지 생성
        message = f"{commenter.nickname} left a comment on your MCP '{mcp_server.name}'."

        return self.notification_dao.create_notification(
            user_id=owner_id,
            notification_type='comment',
            message=message,
            mcp_server_id=mcp_server_id,
            related_user_id=commenter_user_id
        )

    def create_favorite_notification(
        self,
        mcp_server_id: int,
        favoriter_user_id: int
    ) -> Optional[Notification]:
        """즐겨찾기 알림을 생성합니다."""
        # MCP 서버 정보 조회
        mcp_server = self.mcp_dao.get_mcp_server_by_id(mcp_server_id)
        if not mcp_server:
            return None

        # MCP 소유자 ID
        owner_id = mcp_server.owner_id

        # 자기 자신의 즐겨찾기는 알림 생성하지 않음
        if owner_id == favoriter_user_id:
            return None

        # 즐겨찾기한 사용자 정보 조회
        favoriter = self.user_dao.get_user_by_id(favoriter_user_id)
        if not favoriter:
            return None

        # 알림 메시지 생성
        message = f"{favoriter.nickname} added your MCP '{mcp_server.name}' to their favorites."

        return self.notification_dao.create_notification(
            user_id=owner_id,
            notification_type='favorite',
            message=message,
            mcp_server_id=mcp_server_id,
            related_user_id=favoriter_user_id
        )

    def create_status_change_notification(
        self,
        mcp_server_id: int,
        old_status: str,
        new_status: str
    ) -> Optional[Notification]:
        """상태 변경 알림을 생성합니다. (pending → approved)"""
        # pending → approved 변경일 때만 알림 생성
        if old_status != 'pending' or new_status != 'approved':
            return None

        # MCP 서버 정보 조회
        mcp_server = self.mcp_dao.get_mcp_server_by_id(mcp_server_id)
        if not mcp_server:
            return None

        # MCP 소유자 ID
        owner_id = mcp_server.owner_id

        # 알림 메시지 생성
        message = f"Your MCP '{mcp_server.name}' has been approved and is now live."

        return self.notification_dao.create_notification(
            user_id=owner_id,
            notification_type='status_change',
            message=message,
            mcp_server_id=mcp_server_id,
            related_user_id=None
        )

    def create_new_mcp_notification_for_admins(
        self,
        mcp_server_id: int
    ) -> List[Notification]:
        """새 MCP 등록 알림을 관리자들에게 생성합니다."""
        # MCP 서버 정보 조회
        mcp_server = self.mcp_dao.get_mcp_server_by_id(mcp_server_id)
        if not mcp_server:
            return []

        # 등록자 정보 조회
        submitter = self.user_dao.get_user_by_id(mcp_server.owner_id)
        if not submitter:
            return []

        # 모든 관리자 조회
        admins = self.db.query(User).filter(User.is_admin == 'admin').all()

        notifications = []
        for admin in admins:
            # 알림 메시지 생성
            message = f"{submitter.nickname} submitted a new MCP server '{mcp_server.name}' for review."

            notification = self.notification_dao.create_notification(
                user_id=admin.id,
                notification_type='new_mcp',
                message=message,
                mcp_server_id=mcp_server_id,
                related_user_id=submitter.id
            )
            notifications.append(notification)

        return notifications

    def get_user_notifications(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Notification]:
        """사용자의 알림 목록을 조회합니다."""
        return self.notification_dao.get_user_notifications(user_id, limit, offset, unread_only)

    def get_unread_count(self, user_id: int) -> int:
        """읽지 않은 알림 개수를 조회합니다."""
        return self.notification_dao.get_unread_count(user_id)

    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """알림을 읽음으로 표시합니다."""
        return self.notification_dao.mark_as_read(notification_id, user_id)

    def mark_all_as_read(self, user_id: int) -> int:
        """사용자의 모든 알림을 읽음으로 표시합니다."""
        return self.notification_dao.mark_all_as_read(user_id)

    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """알림을 삭제합니다."""
        return self.notification_dao.delete_notification(notification_id, user_id)
