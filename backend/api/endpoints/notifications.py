from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from backend.database import get_db
from backend.database.model import User
from backend.service.notification_service import NotificationService
from backend.api.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Pydantic 스키마
class NotificationResponse(BaseModel):
    id: int
    type: str
    message: str
    is_read: bool
    created_at: str
    mcp_server_id: int | None
    related_user_id: int | None

    class Config:
        from_attributes = True


class UnreadCountResponse(BaseModel):
    count: int


class MarkReadResponse(BaseModel):
    success: bool
    message: str


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = Query(20, description="조회 개수"),
    offset: int = Query(0, description="오프셋"),
    unread_only: bool = Query(False, description="읽지 않은 알림만 조회"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자의 알림 목록을 조회합니다."""
    notification_service = NotificationService(db)

    notifications = notification_service.get_user_notifications(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        unread_only=unread_only
    )

    return [
        NotificationResponse(
            id=notification.id,
            type=notification.type,
            message=notification.message,
            is_read=notification.is_read,
            created_at=notification.created_at.isoformat(),
            mcp_server_id=notification.mcp_server_id,
            related_user_id=notification.related_user_id
        )
        for notification in notifications
    ]


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """읽지 않은 알림 개수를 조회합니다."""
    notification_service = NotificationService(db)
    count = notification_service.get_unread_count(current_user.id)
    return UnreadCountResponse(count=count)


@router.post("/{notification_id}/read", response_model=MarkReadResponse)
async def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """알림을 읽음으로 표시합니다."""
    notification_service = NotificationService(db)
    success = notification_service.mark_as_read(notification_id, current_user.id)

    if success:
        return MarkReadResponse(success=True, message="알림이 읽음으로 표시되었습니다.")
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="알림을 찾을 수 없습니다."
        )


@router.post("/read-all", response_model=MarkReadResponse)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """모든 알림을 읽음으로 표시합니다."""
    notification_service = NotificationService(db)
    count = notification_service.mark_all_as_read(current_user.id)
    return MarkReadResponse(
        success=True,
        message=f"{count}개의 알림이 읽음으로 표시되었습니다."
    )


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """알림을 삭제합니다."""
    notification_service = NotificationService(db)
    success = notification_service.delete_notification(notification_id, current_user.id)

    if success:
        return {"message": "알림이 삭제되었습니다."}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="알림을 찾을 수 없습니다."
        )
