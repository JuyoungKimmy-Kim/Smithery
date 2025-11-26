"""
Analytics Views - TimescaleDB Continuous Aggregates

이 모듈은 TimescaleDB의 continuous aggregate 뷰들을 SQLAlchemy 모델로 정의합니다.
실제 뷰는 001_create_analytics_timescale.sql에서 생성되며,
이 클래스들은 ORM 스타일로 뷰를 조회하기 위한 매핑입니다.

주의:
- 이 모델들은 읽기 전용입니다 (materialized view)
- 실제 뷰 생성은 SQL migration 파일에서 수행됩니다
- 뷰는 TimescaleDB의 refresh policy에 따라 자동으로 업데이트됩니다
"""
from sqlalchemy import Column, Integer, String, DateTime
from .base import Base


class HourlyEventsView(Base):
    """
    시간별 이벤트 집계 뷰 (hourly_events)

    TimescaleDB continuous aggregate로 1시간 단위로 이벤트를 집계합니다.
    5분마다 자동 갱신됩니다.

    원본 SQL:
        CREATE MATERIALIZED VIEW hourly_events
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 hour', created_at) AS hour,
            event_type,
            user_id,
            COUNT(*) as event_count,
            COUNT(DISTINCT user_id) as unique_users
        FROM analytics_events
        GROUP BY hour, event_type, user_id
    """
    __tablename__ = 'hourly_events'
    __table_args__ = {'info': {'is_view': True}}

    hour = Column(DateTime, primary_key=True)
    event_type = Column(String, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    event_count = Column(Integer, nullable=False)
    unique_users = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<HourlyEventsView(hour={self.hour}, type={self.event_type}, count={self.event_count})>"


class DailySearchKeywordsView(Base):
    """
    일별 검색 키워드 집계 뷰 (daily_search_keywords)

    TimescaleDB continuous aggregate로 1일 단위로 검색 키워드를 집계합니다.
    30분마다 자동 갱신됩니다.

    원본 SQL:
        CREATE MATERIALIZED VIEW daily_search_keywords
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 day', created_at) AS day,
            event_metadata->>'keyword' AS keyword,
            COUNT(*) as search_count
        FROM analytics_events
        WHERE event_type IN ('search', 'search_no_results')
            AND event_metadata IS NOT NULL
            AND event_metadata->>'keyword' IS NOT NULL
        GROUP BY day, keyword
    """
    __tablename__ = 'daily_search_keywords'
    __table_args__ = {'info': {'is_view': True}}

    day = Column(DateTime, primary_key=True)
    keyword = Column(String, primary_key=True)
    search_count = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<DailySearchKeywordsView(day={self.day}, keyword={self.keyword}, count={self.search_count})>"


class DailyServerViewsView(Base):
    """
    일별 서버 조회수 집계 뷰 (daily_server_views)

    TimescaleDB continuous aggregate로 1일 단위로 서버 조회수를 집계합니다.
    30분마다 자동 갱신됩니다.

    원본 SQL:
        CREATE MATERIALIZED VIEW daily_server_views
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 day', created_at) AS day,
            (event_metadata->>'mcp_server_id')::INTEGER AS mcp_server_id,
            event_type,
            COUNT(*) as view_count
        FROM analytics_events
        WHERE event_type IN ('server_view', 'server_view_from_search',
                            'server_view_from_list', 'server_view_direct')
            AND event_metadata IS NOT NULL
            AND event_metadata->>'mcp_server_id' IS NOT NULL
        GROUP BY day, mcp_server_id, event_type
    """
    __tablename__ = 'daily_server_views'
    __table_args__ = {'info': {'is_view': True}}

    day = Column(DateTime, primary_key=True)
    mcp_server_id = Column(Integer, primary_key=True)
    event_type = Column(String, primary_key=True)
    view_count = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<DailyServerViewsView(day={self.day}, server={self.mcp_server_id}, count={self.view_count})>"


class DailyUserActionsView(Base):
    """
    일별 사용자 액션 집계 뷰 (daily_user_actions)

    TimescaleDB continuous aggregate로 1일 단위로 사용자 액션을 집계합니다.
    30분마다 자동 갱신됩니다.

    원본 SQL:
        CREATE MATERIALIZED VIEW daily_user_actions
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 day', created_at) AS day,
            event_type,
            (event_metadata->>'mcp_server_id')::INTEGER AS mcp_server_id,
            COUNT(*) as action_count,
            COUNT(DISTINCT user_id) as unique_users
        FROM analytics_events
        WHERE event_type IN ('favorite_add', 'favorite_remove',
                            'comment_add', 'comment_delete', 'playground_query')
            AND event_metadata IS NOT NULL
        GROUP BY day, event_type, mcp_server_id
    """
    __tablename__ = 'daily_user_actions'
    __table_args__ = {'info': {'is_view': True}}

    day = Column(DateTime, primary_key=True)
    event_type = Column(String, primary_key=True)
    mcp_server_id = Column(Integer, primary_key=True)
    action_count = Column(Integer, nullable=False)
    unique_users = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<DailyUserActionsView(day={self.day}, type={self.event_type}, count={self.action_count})>"
