"""
Analytics Event Models for User Behavior Tracking

이 모듈은 확장 가능한 분석 시스템을 위한 데이터 모델을 정의합니다.
새로운 분석 타입을 추가할 때는 EventType enum에 타입만 추가하면 됩니다.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import json

from .base import Base


class EventType(str, enum.Enum):
    """
    이벤트 타입 정의

    새로운 분석을 추가할 때 여기에 타입만 추가하면 됩니다.
    """
    # Search related
    SEARCH = "search"
    SEARCH_NO_RESULTS = "search_no_results"

    # Server view related
    SERVER_VIEW = "server_view"
    SERVER_VIEW_FROM_SEARCH = "server_view_from_search"
    SERVER_VIEW_FROM_LIST = "server_view_from_list"
    SERVER_VIEW_DIRECT = "server_view_direct"

    # User action related
    FAVORITE_ADD = "favorite_add"
    FAVORITE_REMOVE = "favorite_remove"
    COMMENT_ADD = "comment_add"
    COMMENT_DELETE = "comment_delete"

    # User registration/auth
    USER_REGISTER = "user_register"
    USER_LOGIN = "user_login"

    # Playground related
    PLAYGROUND_QUERY = "playground_query"

    # Future extensibility examples:
    # TOOL_EXECUTE = "tool_execute"
    # API_CALL = "api_call"
    # EXPORT_DATA = "export_data"


class AnalyticsEvent(Base):
    """
    범용 분석 이벤트 테이블

    모든 사용자 행동을 기록하는 중앙 테이블입니다.
    metadata 필드에 JSON으로 추가 정보를 저장하여 유연하게 확장 가능합니다.

    예시:
    - SEARCH 이벤트: metadata = {"keyword": "weather", "tags": ["api"], "results_count": 5}
    - SERVER_VIEW 이벤트: metadata = {"mcp_server_id": 123, "referrer": "search"}
    - FAVORITE_ADD 이벤트: metadata = {"mcp_server_id": 123}
    """
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)

    # 이벤트 기본 정보
    event_type = Column(SQLEnum(EventType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)

    # 사용자 정보 (nullable - 비로그인 사용자 허용)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Referrer (유입 경로 분석용)
    referrer = Column(String(512), nullable=True)

    # 추가 메타데이터 (JSON 형식으로 유연하게 저장)
    # 예: {"keyword": "weather", "tags": ["api"], "results_count": 5}
    event_metadata = Column(Text, nullable=True)  # JSON string

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", backref="analytics_events")

    # 복합 인덱스 (시계열 분석 성능 최적화)
    __table_args__ = (
        Index('ix_event_type_created_at', 'event_type', 'created_at'),
        Index('ix_user_event_created_at', 'user_id', 'event_type', 'created_at'),
    )

    def set_metadata(self, data: dict):
        """메타데이터를 JSON 문자열로 저장"""
        self.event_metadata = json.dumps(data) if data else None

    def get_metadata(self) -> dict:
        """메타데이터를 딕셔너리로 반환"""
        if self.event_metadata:
            try:
                return json.loads(self.event_metadata)
            except json.JSONDecodeError:
                return {}
        return {}

    def __repr__(self):
        return f"<AnalyticsEvent(id={self.id}, type={self.event_type}, user_id={self.user_id}, created_at={self.created_at})>"
