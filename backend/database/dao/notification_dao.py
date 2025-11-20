from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional, List
from backend.database.model.notification import Notification

class NotificationDAO:
    def __init__(self, db: Session):
        self.db = db

    def create_notification(
        self,
        user_id: int,
        notification_type: str,
        message: str,
        mcp_server_id: Optional[int] = None,
        related_user_id: Optional[int] = None
    ) -> Notification:
        """새 알림을 생성합니다."""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            message=message,
            mcp_server_id=mcp_server_id,
            related_user_id=related_user_id,
            is_read=False
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_user_notifications(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Notification]:
        """사용자의 알림 목록을 조회합니다."""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.is_read == False)

        return query.order_by(desc(Notification.created_at)).limit(limit).offset(offset).all()

    def get_unread_count(self, user_id: int) -> int:
        """읽지 않은 알림 개수를 조회합니다."""
        return self.db.query(Notification).filter(
            and_(Notification.user_id == user_id, Notification.is_read == False)
        ).count()

    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """알림을 읽음으로 표시합니다."""
        notification = self.db.query(Notification).filter(
            and_(Notification.id == notification_id, Notification.user_id == user_id)
        ).first()

        if notification:
            notification.is_read = True
            self.db.commit()
            return True
        return False

    def mark_all_as_read(self, user_id: int) -> int:
        """사용자의 모든 알림을 읽음으로 표시합니다."""
        count = self.db.query(Notification).filter(
            and_(Notification.user_id == user_id, Notification.is_read == False)
        ).update({'is_read': True})
        self.db.commit()
        return count

    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """알림을 삭제합니다."""
        notification = self.db.query(Notification).filter(
            and_(Notification.id == notification_id, Notification.user_id == user_id)
        ).first()

        if notification:
            self.db.delete(notification)
            self.db.commit()
            return True
        return False

    def delete_old_notifications(self, user_id: int, days: int = 30) -> int:
        """오래된 알림을 삭제합니다. (기본 30일)"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        count = self.db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.created_at < cutoff_date,
                Notification.is_read == True  # 읽은 알림만 삭제
            )
        ).delete()
        self.db.commit()
        return count
