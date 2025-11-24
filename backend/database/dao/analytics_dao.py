"""
Analytics DAO - Data Access Layer for Analytics

이 DAO는 분석 이벤트의 저장 및 조회를 담당합니다.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, distinct
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from backend.database.model import AnalyticsEvent, AnalyticsAggregation, EventType


class AnalyticsDAO:
    """Analytics 데이터 접근 객체"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Event Creation ====================

    def create_event(
        self,
        event_type: EventType,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalyticsEvent:
        """
        새로운 분석 이벤트를 생성합니다.

        Args:
            event_type: 이벤트 타입 (EventType enum)
            user_id: 사용자 ID (선택사항, 비로그인 허용)
            session_id: 세션 ID (사용자 여정 추적용)
            ip_address: IP 주소
            user_agent: User-Agent 문자열
            referrer: Referrer URL
            metadata: 추가 메타데이터 (딕셔너리)

        Returns:
            생성된 AnalyticsEvent 객체
        """
        event = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
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

    def get_events_by_session(
        self,
        session_id: str
    ) -> List[AnalyticsEvent]:
        """특정 세션의 모든 이벤트를 조회합니다 (사용자 여정 추적용)."""
        return self.db.query(AnalyticsEvent).filter(
            AnalyticsEvent.session_id == session_id
        ).order_by(AnalyticsEvent.created_at).all()

    # ==================== Aggregation Queries ====================

    def count_events_by_type(
        self,
        event_type: EventType,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """특정 타입의 이벤트 수를 집계합니다."""
        query = self.db.query(func.count(AnalyticsEvent.id)).filter(
            AnalyticsEvent.event_type == event_type
        )

        if start_date:
            query = query.filter(AnalyticsEvent.created_at >= start_date)
        if end_date:
            query = query.filter(AnalyticsEvent.created_at <= end_date)

        return query.scalar() or 0

    def get_top_search_keywords(
        self,
        limit: int = 10,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        가장 많이 검색된 키워드를 조회합니다.

        Returns:
            [{"keyword": "weather", "count": 150}, ...]
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        events = self.db.query(AnalyticsEvent).filter(
            and_(
                AnalyticsEvent.event_type == EventType.SEARCH,
                AnalyticsEvent.created_at >= start_date
            )
        ).all()

        # 메타데이터에서 키워드 추출 및 집계
        keyword_counts = {}
        for event in events:
            metadata = event.get_metadata()
            keyword = metadata.get("keyword", "").strip().lower()
            if keyword:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        # 정렬 및 상위 N개 반환
        sorted_keywords = sorted(
            keyword_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [{"keyword": k, "count": c} for k, c in sorted_keywords]

    def get_most_viewed_servers(
        self,
        limit: int = 10,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        가장 많이 조회된 서버를 조회합니다.

        Returns:
            [{"mcp_server_id": 123, "view_count": 500}, ...]
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        events = self.db.query(AnalyticsEvent).filter(
            and_(
                AnalyticsEvent.event_type.in_([
                    EventType.SERVER_VIEW,
                    EventType.SERVER_VIEW_FROM_SEARCH,
                    EventType.SERVER_VIEW_FROM_LIST,
                    EventType.SERVER_VIEW_DIRECT
                ]),
                AnalyticsEvent.created_at >= start_date
            )
        ).all()

        # 메타데이터에서 서버 ID 추출 및 집계
        server_counts = {}
        for event in events:
            metadata = event.get_metadata()
            server_id = metadata.get("mcp_server_id")
            if server_id:
                server_counts[server_id] = server_counts.get(server_id, 0) + 1

        # 정렬 및 상위 N개 반환
        sorted_servers = sorted(
            server_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [{"mcp_server_id": s_id, "view_count": count} for s_id, count in sorted_servers]

    def get_unique_visitors_count(
        self,
        days: int = 7
    ) -> Dict[str, int]:
        """
        고유 방문자 수를 집계합니다.

        Returns:
            {"logged_in_users": 50, "anonymous_users": 200, "total_sessions": 250}
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # 로그인 사용자 수
        logged_in_count = self.db.query(
            func.count(distinct(AnalyticsEvent.user_id))
        ).filter(
            and_(
                AnalyticsEvent.user_id.isnot(None),
                AnalyticsEvent.created_at >= start_date
            )
        ).scalar() or 0

        # 전체 세션 수
        total_sessions = self.db.query(
            func.count(distinct(AnalyticsEvent.session_id))
        ).filter(
            and_(
                AnalyticsEvent.session_id.isnot(None),
                AnalyticsEvent.created_at >= start_date
            )
        ).scalar() or 0

        # 익명 사용자는 전체 세션에서 로그인 사용자 수를 뺀 값 (근사치)
        anonymous_count = max(0, total_sessions - logged_in_count)

        return {
            "logged_in_users": logged_in_count,
            "anonymous_users": anonymous_count,
            "total_sessions": total_sessions
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

    # ==================== Aggregation Table Operations ====================

    def create_or_update_aggregation(
        self,
        aggregation_type: str,
        aggregation_key: str,
        aggregation_value: int,
        aggregation_date: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalyticsAggregation:
        """
        집계 데이터를 생성하거나 업데이트합니다.

        동일한 type, key, date 조합이 있으면 업데이트, 없으면 생성합니다.
        """
        existing = self.db.query(AnalyticsAggregation).filter(
            and_(
                AnalyticsAggregation.aggregation_type == aggregation_type,
                AnalyticsAggregation.aggregation_key == aggregation_key,
                AnalyticsAggregation.aggregation_date == aggregation_date
            )
        ).first()

        if existing:
            # 업데이트
            existing.aggregation_value = aggregation_value
            existing.updated_at = datetime.utcnow()
            if metadata:
                existing.set_metadata(metadata)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # 생성
            agg = AnalyticsAggregation(
                aggregation_type=aggregation_type,
                aggregation_key=aggregation_key,
                aggregation_value=aggregation_value,
                aggregation_date=aggregation_date
            )
            if metadata:
                agg.set_metadata(metadata)
            self.db.add(agg)
            self.db.commit()
            self.db.refresh(agg)
            return agg

    def get_aggregations(
        self,
        aggregation_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AnalyticsAggregation]:
        """특정 타입의 집계 데이터를 조회합니다."""
        query = self.db.query(AnalyticsAggregation).filter(
            AnalyticsAggregation.aggregation_type == aggregation_type
        )

        if start_date:
            query = query.filter(AnalyticsAggregation.aggregation_date >= start_date)
        if end_date:
            query = query.filter(AnalyticsAggregation.aggregation_date <= end_date)

        return query.order_by(
            desc(AnalyticsAggregation.aggregation_value)
        ).limit(limit).all()
