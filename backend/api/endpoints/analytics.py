"""
Analytics API Endpoints

이 모듈은 분석 데이터를 조회하는 REST API를 제공합니다.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from backend.database import get_db
from backend.service.analytics_service import AnalyticsService
from backend.api.auth import get_current_admin_user
from backend.database.model import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/search/top-keywords")
def get_top_search_keywords(
    limit: int = Query(10, ge=1, le=100, description="조회할 키워드 수"),
    days: int = Query(7, ge=1, le=365, description="분석 기간 (일)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Admin only
):
    """
    가장 많이 검색된 키워드를 조회합니다. (관리자 전용)

    Returns:
        [{"keyword": "weather", "count": 150}, ...]
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_top_search_keywords(limit, days)


@router.get("/servers/most-viewed")
def get_most_viewed_servers(
    limit: int = Query(10, ge=1, le=100, description="조회할 서버 수"),
    days: int = Query(7, ge=1, le=365, description="분석 기간 (일)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Admin only
):
    """
    가장 많이 조회된 서버를 조회합니다. (관리자 전용)

    Returns:
        [{"mcp_server_id": 123, "view_count": 500}, ...]
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_most_viewed_servers(limit, days)


@router.get("/servers/trending")
def get_trending_servers(
    limit: int = Query(10, ge=1, le=100, description="조회할 서버 수"),
    days: int = Query(7, ge=1, le=30, description="최근 기간 (일)"),
    comparison_days: int = Query(7, ge=1, le=30, description="비교 기간 (일)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Admin only
):
    """
    급상승 중인 서버를 조회합니다. (관리자 전용)

    최근 N일의 조회수와 그 이전 N일을 비교하여 증가율이 높은 서버를 반환합니다.

    Returns:
        [{"mcp_server_id": 123, "recent_views": 100, "previous_views": 20, "growth_rate": 4.0}, ...]
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_trending_servers(limit, days, comparison_days)


@router.get("/conversion/search-to-view")
def get_search_to_view_conversion(
    days: int = Query(7, ge=1, le=365, description="분석 기간 (일)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Admin only
):
    """
    검색 후 서버 조회 전환율을 조회합니다. (관리자 전용)

    Returns:
        {
            "searches": 1000,
            "views": 300,
            "conversion_rate": 0.3
        }
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_search_to_view_conversion_rate(days)


@router.get("/user-journey/{session_id}")
def get_user_journey(
    session_id: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Admin only
):
    """
    특정 세션의 사용자 여정을 조회합니다. (관리자 전용)

    Returns:
        [
            {"event_type": "search", "timestamp": "...", "metadata": {...}},
            {"event_type": "server_view", "timestamp": "...", "metadata": {...}},
            ...
        ]
    """
    analytics_service = AnalyticsService(db)
    journey = analytics_service.get_user_journey(session_id)

    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No user journey found for session_id: {session_id}"
        )

    return journey


@router.get("/summary")
def get_analytics_summary(
    days: int = Query(7, ge=1, le=365, description="분석 기간 (일)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)  # Admin only
):
    """
    전체 분석 요약 정보를 조회합니다. (관리자 전용)

    대시보드에 표시할 종합 정보를 제공합니다.

    Returns:
        {
            "period_days": 7,
            "events": {
                "searches": 1500,
                "server_views": 450,
                "favorites": 120,
                "comments": 35,
                "playground_queries": 80
            },
            "visitors": {
                "logged_in_users": 50,
                "anonymous_users": 200,
                "total_sessions": 250
            },
            "top_keywords": [...],
            "top_servers": [...],
            "conversion_rate": {...}
        }
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_analytics_summary(days)


# Public endpoints (no auth required) - for frontend display

@router.get("/public/trending-servers")
def get_public_trending_servers(
    limit: int = Query(5, ge=1, le=20, description="조회할 서버 수"),
    days: int = Query(7, ge=1, le=30, description="분석 기간"),
    db: Session = Depends(get_db)
):
    """
    급상승 중인 서버를 조회합니다. (공개 API)

    프론트엔드에서 트렌딩 섹션을 표시하기 위한 공개 API입니다.
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_trending_servers(limit, days)


@router.get("/public/popular-searches")
def get_public_popular_searches(
    limit: int = Query(5, ge=1, le=20, description="조회할 키워드 수"),
    days: int = Query(7, ge=1, le=30, description="분석 기간"),
    db: Session = Depends(get_db)
):
    """
    인기 검색어를 조회합니다. (공개 API)

    프론트엔드에서 인기 검색어를 표시하기 위한 공개 API입니다.
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_top_search_keywords(limit, days)
