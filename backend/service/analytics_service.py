"""
Analytics Service - Business Logic Layer for Analytics

이 서비스는 분석 이벤트 추적 및 집계를 담당합니다.
확장 가능한 구조로 설계되어 새로운 분석 타입 추가가 용이합니다.
"""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from backend.database.dao.analytics_dao import AnalyticsDAO
from backend.database.model import EventType

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Analytics 비즈니스 로직 서비스

    사용법:
        analytics = AnalyticsService(db)

        # 이벤트 추적
        analytics.track_search(user_id=1, keyword="weather", results_count=5)
        analytics.track_server_view(user_id=1, mcp_server_id=123, referrer="search")

        # 분석 데이터 조회
        top_keywords = analytics.get_top_search_keywords(limit=10, days=7)
        trending_servers = analytics.get_trending_servers(days=7)
    """

    def __init__(self, db: Session):
        self.db = db
        self.dao = AnalyticsDAO(db)

    # ==================== Tracking Methods ====================

    def track_event(
        self,
        event_type: EventType,
        user_id: Optional[int] = None,
        referrer: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        범용 이벤트 추적 메서드

        모든 이벤트는 이 메서드를 통해 기록될 수 있습니다.
        특정 이벤트 타입을 위한 편의 메서드들도 제공됩니다.
        """
        try:
            self.dao.create_event(
                event_type=event_type,
                user_id=user_id,
                referrer=referrer,
                metadata=metadata
            )
            logger.info(f"Tracked event: {event_type.value}, user_id={user_id}, metadata={metadata}")
        except Exception as e:
            logger.error(f"Failed to track event {event_type.value}: {e}")
            # 분석 실패가 메인 기능을 방해하지 않도록 예외를 삼킴

    def track_search(
        self,
        keyword: str,
        results_count: int,
        user_id: Optional[int] = None,
        tags: Optional[List[str]] = None
    ):
        """검색 이벤트를 추적합니다."""
        metadata = {
            "keyword": keyword,
            "results_count": results_count
        }
        if tags:
            metadata["tags"] = tags

        event_type = EventType.SEARCH_NO_RESULTS if results_count == 0 else EventType.SEARCH

        self.track_event(
            event_type=event_type,
            user_id=user_id,
            metadata=metadata
        )

    def track_server_view(
        self,
        mcp_server_id: int,
        user_id: Optional[int] = None,
        referrer: Optional[str] = None
    ):
        """서버 조회 이벤트를 추적합니다."""
        # Referrer에 따라 이벤트 타입 결정
        if referrer and "search" in referrer.lower():
            event_type = EventType.SERVER_VIEW_FROM_SEARCH
        elif referrer and "list" in referrer.lower():
            event_type = EventType.SERVER_VIEW_FROM_LIST
        elif referrer:
            event_type = EventType.SERVER_VIEW_DIRECT
        else:
            event_type = EventType.SERVER_VIEW

        metadata = {
            "mcp_server_id": mcp_server_id
        }

        self.track_event(
            event_type=event_type,
            user_id=user_id,
            referrer=referrer,
            metadata=metadata
        )

    def track_favorite_add(
        self,
        mcp_server_id: int,
        user_id: int
    ):
        """즐겨찾기 추가 이벤트를 추적합니다."""
        self.track_event(
            event_type=EventType.FAVORITE_ADD,
            user_id=user_id,
            metadata={"mcp_server_id": mcp_server_id}
        )

    def track_favorite_remove(
        self,
        mcp_server_id: int,
        user_id: int
    ):
        """즐겨찾기 제거 이벤트를 추적합니다."""
        self.track_event(
            event_type=EventType.FAVORITE_REMOVE,
            user_id=user_id,
            metadata={"mcp_server_id": mcp_server_id}
        )

    def track_comment_add(
        self,
        mcp_server_id: int,
        user_id: int
    ):
        """댓글 추가 이벤트를 추적합니다."""
        self.track_event(
            event_type=EventType.COMMENT_ADD,
            user_id=user_id,
            metadata={"mcp_server_id": mcp_server_id}
        )

    def track_comment_delete(
        self,
        mcp_server_id: int,
        user_id: int
    ):
        """댓글 삭제 이벤트를 추적합니다."""
        self.track_event(
            event_type=EventType.COMMENT_DELETE,
            user_id=user_id,
            metadata={"mcp_server_id": mcp_server_id}
        )

    def track_playground_query(
        self,
        mcp_server_id: int,
        user_id: int,
        query_tokens: Optional[int] = None
    ):
        """Playground 쿼리 이벤트를 추적합니다."""
        metadata = {"mcp_server_id": mcp_server_id}
        if query_tokens:
            metadata["query_tokens"] = query_tokens

        self.track_event(
            event_type=EventType.PLAYGROUND_QUERY,
            user_id=user_id,
            metadata=metadata
        )

    def track_user_register(
        self,
        user_id: int,
        registration_method: str = "email"
    ):
        """사용자 등록 이벤트를 추적합니다."""
        self.track_event(
            event_type=EventType.USER_REGISTER,
            user_id=user_id,
            metadata={"registration_method": registration_method}
        )

    def track_user_login(
        self,
        user_id: int
    ):
        """사용자 로그인 이벤트를 추적합니다."""
        self.track_event(
            event_type=EventType.USER_LOGIN,
            user_id=user_id
        )

    # ==================== Analytics & Insights ====================

    def get_top_search_keywords(
        self,
        limit: int = 10,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        가장 인기 있는 검색 키워드를 조회합니다.

        Returns:
            [{"keyword": "weather", "count": 150}, ...]
        """
        return self.dao.get_top_search_keywords(limit, days)

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
        return self.dao.get_most_viewed_servers(limit, days)

    def get_trending_servers(
        self,
        limit: int = 10,
        days: int = 7,
        comparison_days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        급상승 중인 서버를 조회합니다.

        최근 N일의 조회수와 그 이전 N일의 조회수를 비교하여
        증가율이 높은 서버를 반환합니다.

        Returns:
            [{"mcp_server_id": 123, "recent_views": 100, "previous_views": 20, "growth_rate": 4.0}, ...]
        """
        # 최근 기간의 조회수
        recent_servers = self.dao.get_most_viewed_servers(limit=100, days=days)
        recent_views = {s["mcp_server_id"]: s["view_count"] for s in recent_servers}

        # 비교 기간의 조회수 (days+1 ~ days+comparison_days+1)
        # 이를 위해 더 긴 기간을 조회한 후 차이를 계산
        total_days = days + comparison_days
        total_servers = self.dao.get_most_viewed_servers(limit=100, days=total_days)
        total_views = {s["mcp_server_id"]: s["view_count"] for s in total_servers}

        # 증가율 계산
        trending = []
        for server_id in recent_views.keys():
            recent = recent_views[server_id]
            total = total_views.get(server_id, recent)
            previous = max(1, total - recent)  # 0으로 나누기 방지

            growth_rate = recent / previous

            trending.append({
                "mcp_server_id": server_id,
                "recent_views": recent,
                "previous_views": previous,
                "growth_rate": round(growth_rate, 2)
            })

        # 증가율 기준 정렬
        trending.sort(key=lambda x: x["growth_rate"], reverse=True)

        return trending[:limit]

    def get_search_to_view_conversion_rate(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        검색 후 서버 조회 전환율을 계산합니다.

        Returns:
            {
                "searches": 1000,
                "views": 300,
                "conversion_rate": 0.3
            }
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        searches = self.dao.count_events_by_type(EventType.SEARCH, start_date)

        # 모든 타입의 서버 조회 합산
        views = sum([
            self.dao.count_events_by_type(EventType.SERVER_VIEW, start_date),
            self.dao.count_events_by_type(EventType.SERVER_VIEW_FROM_SEARCH, start_date),
            self.dao.count_events_by_type(EventType.SERVER_VIEW_FROM_LIST, start_date),
            self.dao.count_events_by_type(EventType.SERVER_VIEW_DIRECT, start_date)
        ])

        conversion_rate = (views / searches) if searches > 0 else 0.0

        return {
            "searches": searches,
            "views": views,
            "conversion_rate": round(conversion_rate, 4)
        }


    def get_analytics_summary(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        전체 분석 요약 정보를 반환합니다.

        대시보드에 표시할 수 있는 종합 정보를 제공합니다.
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # 각종 이벤트 수 집계
        searches = self.dao.count_events_by_type(EventType.SEARCH, start_date)
        server_views = sum([
            self.dao.count_events_by_type(EventType.SERVER_VIEW, start_date),
            self.dao.count_events_by_type(EventType.SERVER_VIEW_FROM_SEARCH, start_date),
            self.dao.count_events_by_type(EventType.SERVER_VIEW_FROM_LIST, start_date),
            self.dao.count_events_by_type(EventType.SERVER_VIEW_DIRECT, start_date)
        ])
        favorites = self.dao.count_events_by_type(EventType.FAVORITE_ADD, start_date)
        comments = self.dao.count_events_by_type(EventType.COMMENT_ADD, start_date)
        playground_queries = self.dao.count_events_by_type(EventType.PLAYGROUND_QUERY, start_date)

        # 방문자 통계
        visitors = self.dao.get_unique_visitors_count(days)

        # 인기 컨텐츠
        top_keywords = self.get_top_search_keywords(limit=5, days=days)
        top_servers = self.get_most_viewed_servers(limit=5, days=days)

        # 전환율
        conversion = self.get_search_to_view_conversion_rate(days)

        return {
            "period_days": days,
            "events": {
                "searches": searches,
                "server_views": server_views,
                "favorites": favorites,
                "comments": comments,
                "playground_queries": playground_queries
            },
            "visitors": visitors,
            "top_keywords": top_keywords,
            "top_servers": top_servers,
            "conversion_rate": conversion
        }
