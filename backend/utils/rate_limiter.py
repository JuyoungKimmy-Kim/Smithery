"""
Rate Limiting 유틸리티
사용자별 API 호출 빈도를 제한합니다.
"""
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple
import threading


class RateLimiter:
    """
    간단한 메모리 기반 Rate Limiter
    프로덕션 환경에서는 Redis를 사용하는 것을 권장합니다.
    """
    
    def __init__(self):
        # user_id -> (request_count, window_start_time)
        self._requests: Dict[int, Tuple[int, datetime]] = {}
        self._lock = threading.Lock()
    
    def check_rate_limit(
        self, 
        user_id: int, 
        max_requests: int = 10, 
        window_seconds: int = 60
    ) -> None:
        """
        Rate limit 체크
        
        Args:
            user_id: 사용자 ID
            max_requests: 시간 윈도우당 최대 요청 수
            window_seconds: 시간 윈도우 (초)
            
        Raises:
            HTTPException: Rate limit 초과 시
        """
        with self._lock:
            now = datetime.now()
            
            if user_id not in self._requests:
                self._requests[user_id] = (1, now)
                return
            
            request_count, window_start = self._requests[user_id]
            window_end = window_start + timedelta(seconds=window_seconds)
            
            # 시간 윈도우가 만료되었으면 리셋
            if now >= window_end:
                self._requests[user_id] = (1, now)
                return
            
            # 시간 윈도우 내에서 요청 수 체크
            if request_count >= max_requests:
                remaining_time = int((window_end - now).total_seconds())
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"너무 많은 요청입니다. {remaining_time}초 후에 다시 시도해주세요."
                )
            
            # 요청 수 증가
            self._requests[user_id] = (request_count + 1, window_start)
    
    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """오래된 엔트리 정리 (메모리 관리)"""
        with self._lock:
            now = datetime.now()
            expired_users = [
                user_id for user_id, (_, window_start) in self._requests.items()
                if (now - window_start).total_seconds() > max_age_seconds
            ]
            for user_id in expired_users:
                del self._requests[user_id]


# 전역 Rate Limiter 인스턴스
rate_limiter = RateLimiter()

