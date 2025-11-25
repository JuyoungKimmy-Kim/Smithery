"""
Analytics DAO - Data Access Layer for Analytics

이 DAO는 분석 이벤트의 저장 및 조회를 담당합니다.
TimescaleDB continuous aggregates를 사용하여 빠른 집계 쿼리 제공.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, distinct, text
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from backend.database.model import AnalyticsEvent, EventType


class AnalyticsDAO:
    """Analytics 데이터 접근 객체"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Event Creation ====================

    def create_event(
        self,
        event_type: EventType,
        user_id: Optional[int] = None,
        referrer: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalyticsEvent:
        """
        새로운 분석 이벤트를 생성합니다.

        Args:
            event_type: 이벤트 타입 (EventType enum)
            user_id: 사용자 ID (선택사항, 비로그인 허용)
            referrer: Referrer URL
            metadata: 추가 메타데이터 (딕셔너리)

        Returns:
            생성된 AnalyticsEvent 객체
        """
        event = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            referrer=referrer
        )

        if metadata:
            event.set_metadata(metadata)

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    # ==================== Event Queries ====================

    def get_events_by_type(
        self,
        event_type: EventType,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AnalyticsEvent]:
        """특정 타입의 이벤트를 조회합니다."""
        query = self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.event_type == event_type
        )

        if start_date:
            query = query.filter(AnalyticsEvent.created_at >= start_date)
        if end_date:
            query = query.filter(AnalyticsEvent.created_at <= end_date)

        return query.order_by(desc(AnalyticsEvent.created_at)).limit(limit).offset(offset).all()

    def get_events_by_user(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[AnalyticsEvent]:
        """특정 사용자의 이벤트를 조회합니다."""
        return self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == user_id
        ).order_by(desc(AnalyticsEvent.created_at)).limit(limit).offset(offset).all()

    # ==================== Aggregation Queries ====================

    def count_events_by_type(
        self,
        event_type: EventType,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        특정 타입의 이벤트 수를 집계합니다.
        TimescaleDB hourly_events를 사용하여 빠른 집계.
        """
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=7)

        # Continuous aggregate 사용
        query = text("""
            SELECT COALESCE(SUM(event_count), 0)::INTEGER
            FROM hourly_events
            WHERE event_type = :event_type
                AND hour >= :start_date
                AND (:end_date IS NULL OR hour <= :end_date)
        """)

        result = self.db.execute(query, {
            "event_type": event_type.value,
            "start_date": start_date,
            "end_date": end_date
        })

        return result.scalar() or 0

    def get_top_search_keywords(
        self,
        limit: int = 10,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        가장 많이 검색된 키워드를 조회합니다.
        TimescaleDB continuous aggregate를 사용하여 빠른 조회.

        Returns:
            [{"keyword": "weather", "count": 150}, ...]
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Continuous aggregate 사용
        query = text("""
            SELECT
                keyword,
                SUM(search_count)::INTEGER as count
            FROM daily_search_keywords
            WHERE day >= :start_date
                AND keyword IS NOT NULL
            GROUP BY keyword
            ORDER BY count DESC
            LIMIT :limit
        """)

        result = self.db.execute(query, {"start_date": start_date, "limit": limit})

        return [{"keyword": row[0], "count": row[1]} for row in result]

    def get_most_viewed_servers(
        self,
        limit: int = 10,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        가장 많이 조회된 서버를 조회합니다.
        TimescaleDB continuous aggregate를 사용하여 빠른 조회.

        Returns:
            [{"mcp_server_id": 123, "view_count": 500}, ...]
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Continuous aggregate 사용
        query = text("""
            SELECT
                mcp_server_id,
                SUM(view_count)::INTEGER as view_count
            FROM daily_server_views
            WHERE day >= :start_date
                AND mcp_server_id IS NOT NULL
            GROUP BY mcp_server_id
            ORDER BY view_count DESC
            LIMIT :limit
        """)

        result = self.db.execute(query, {"start_date": start_date, "limit": limit})

        return [{"mcp_server_id": row[0], "view_count": row[1]} for row in result]

    def get_unique_visitors_count(
        self,
        days: int = 7
    ) -> Dict[str, int]:
        """
        고유 방문자 수를 집계합니다.
        TimescaleDB hourly_events를 사용하여 빠른 집계.

        Returns:
            {"logged_in_users": 50}
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Continuous aggregate 사용
        query = text("""
            SELECT COUNT(DISTINCT user_id)::INTEGER
            FROM (
                SELECT DISTINCT user_id, hour
                FROM hourly_events
                WHERE hour >= :start_date
                    AND unique_users > 0
            ) subquery
            WHERE user_id IS NOT NULL
        """)

        result = self.db.execute(query, {"start_date": start_date})
        logged_in_count = result.scalar() or 0

        return {
            "logged_in_users": logged_in_count
        }

    def get_conversion_rate(
        self,
        from_event: EventType,
        to_event: EventType,
        days: int = 7
    ) -> float:
        """
        이벤트 간 전환율을 계산합니다.
        예: 검색 → 서버 조회 전환율

        Returns:
            전환율 (0.0 ~ 1.0)
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        from_count = self.count_events_by_type(from_event, start_date)
        to_count = self.count_events_by_type(to_event, start_date)

        if from_count == 0:
            return 0.0

        return min(1.0, to_count / from_count)
