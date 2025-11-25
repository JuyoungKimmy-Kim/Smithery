# Analytics 시스템 가이드

## 📊 현재 구현 상태 (v1.0)

### ✅ 완료된 기능

1. **실시간 이벤트 추적**
   - `analytics_events` 테이블에 모든 사용자 행동 기록
   - 지원 이벤트: 검색, 서버 조회, 즐겨찾기, 댓글, Playground 등
   - 자동 추적: API 호출 시 자동으로 이벤트 기록

2. **분석 API 제공**
   - 인기 검색어 Top N
   - 가장 많이 조회된 서버
   - 급상승 서버 (트렌딩)
   - 검색 → 조회 전환율
   - 사용자 여정 추적
   - 전체 통계 대시보드

3. **데이터베이스 구조**
   - `analytics_events`: 실시간 이벤트 저장 및 집계

---

## 🔄 현재 동작 방식

### 실시간 집계 방식
```
사용자 행동 발생
    ↓
analytics_events 테이블에 INSERT
    ↓
분석 API 호출 시
    ↓
analytics_events에서 직접 집계 (GROUP BY, COUNT)
    ↓
결과 반환
```

**장점:**
- 구현이 간단함
- 실시간 데이터 반영
- 별도 크론잡 불필요

**단점:**
- 데이터가 많아지면 조회 속도 저하
- 매번 전체 테이블 스캔 필요

---

## 📈 확장 시점 가이드

### 언제 집계 시스템(Aggregation)이 필요한가?

#### Case 1: 서비스 규모가 작을 때 (현재)
- **일일 이벤트 수**: ~10,000건 이하
- **응답 시간**: 1초 이내
- **결론**: **실시간 집계로 충분** ✅

#### Case 2: 서비스 규모가 중간일 때
- **일일 이벤트 수**: 10,000 ~ 100,000건
- **응답 시간**: 1~5초
- **결론**: **인덱스 최적화 + 캐싱 고려**

#### Case 3: 서비스 규모가 클 때
- **일일 이벤트 수**: 100,000건 이상
- **응답 시간**: 5초 이상
- **결론**: **집계 시스템 필수** 🚨

---

## 🗄️ 데이터 보관 정책

### analytics_events 테이블

#### 권장 보관 기간

| 서비스 규모 | 보관 기간 | 삭제 주기 | 이유 |
|------------|----------|----------|------|
| **Small** (~10K/day) | **90일** | 월 1회 | 디스크 공간 충분, 장기 분석 가능 |
| **Medium** (10K~100K/day) | **30일** | 주 1회 | 디스크 공간 관리, 최근 데이터 중심 |
| **Large** (100K+/day) | **7일** | 매일 | 디스크 절약, 집계 데이터 활용 |

#### 삭제 전 체크리스트
1. ✅ 백업 필요 시 S3/외부 저장소에 아카이브
2. ✅ 중요 이벤트 (회원가입, 결제 등) 별도 보관 고려
3. ✅ 집계 시스템 도입 시: 집계 완료 후 삭제


---

## 🚀 집계 시스템 도입 가이드 (향후 확장)

### 1단계: 집계 크론잡 구현

#### A. 필요한 라이브러리
```bash
pip install APScheduler
```

#### B. 집계 테이블 추가
먼저 `AnalyticsAggregation` 모델을 추가해야 합니다:
```python
# backend/database/model/analytics_event.py
class AnalyticsAggregation(Base):
    __tablename__ = "analytics_aggregations"
    id = Column(Integer, primary_key=True)
    aggregation_type = Column(String(100), nullable=False)
    aggregation_key = Column(String(255), nullable=False)
    aggregation_value = Column(Integer, default=0)
    aggregation_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

#### C. 집계 스크립트 작성
`backend/service/analytics_aggregation_job.py` 생성:
- 일별 서버 조회수 집계
- 일별 검색어 집계
- 일별 즐겨찾기 집계
- 일별 전체 통계 집계

#### D. 스케줄러 설정
`backend/scheduler.py` 생성:
- **매일 자정(UTC)**: 어제 데이터 집계
- **매주 일요일 새벽**: 오래된 이벤트 삭제

#### E. FastAPI 통합
`backend/main.py`에 스케줄러 시작/중지 추가:
```python
@app.on_event("startup")
async def startup_event():
    from backend.scheduler import start_scheduler
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    from backend.scheduler import stop_scheduler
    stop_scheduler()
```

### 2단계: 분석 API 수정

#### Before (현재 - 실시간 집계)
```python
def get_top_search_keywords(days=7):
    # analytics_events에서 직접 집계
    events = db.query(AnalyticsEvent).filter(...)
    # GROUP BY 처리...
```

#### After (확장 후 - 집계 테이블 사용)
```python
def get_top_search_keywords(days=7):
    # analytics_aggregations에서 조회 (빠름!)
    aggregations = db.query(AnalyticsAggregation).filter(
        aggregation_type="daily_search_keywords",
        aggregation_date >= start_date
    )
    # 이미 집계된 데이터 반환
```

### 3단계: 성능 비교 및 모니터링

- 응답 시간 측정
- 데이터베이스 부하 확인
- 디스크 사용량 모니터링

---

## 📊 데이터 라이프사이클 예시

### Small Service (현재)
```
[실시간 수집] analytics_events (90일 보관)
                    ↓ API 조회 시 집계
              [분석 API 결과]
```

### Large Service (확장 시)
```
[실시간 수집] analytics_events (7일 보관)
                    ↓ 매일 자정 집계
         analytics_aggregations (영구 보관)
                    ↓ API 조회 시
              [분석 API 결과]

* 7일 지난 events는 자동 삭제
* 집계 데이터로 장기 트렌드 분석 가능
* AnalyticsAggregation 모델 추가 필요
```

---

## 🔍 성능 최적화 체크리스트

### 현재 시점에서 할 수 있는 것

✅ **이미 적용됨:**
1. 복합 인덱스 (event_type + created_at)
2. 사용자별 인덱스 (user_id + event_type + created_at)
3. 세션별 인덱스 (session_id + created_at)

✅ **추가 고려사항:**
1. **쿼리 캐싱**: Redis/Memcached로 자주 조회되는 통계 캐싱
2. **파티셔닝**: 날짜별 테이블 파티션 (PostgreSQL)
3. **읽기 전용 복제**: 분석 쿼리용 Read Replica

---

## 💡 권장 마일스톤

### Phase 1: 현재 (실시간 집계)
- [x] 이벤트 추적 구현
- [x] 분석 API 구현
- [x] 인덱스 최적화
- [ ] 성능 모니터링 설정

### Phase 2: 성능 개선 (10K+ events/day)
- [ ] 쿼리 캐싱 (Redis)
- [ ] 응답 시간 모니터링
- [ ] 느린 쿼리 최적화

### Phase 3: 확장 (100K+ events/day)
- [ ] 집계 크론잡 구현
- [ ] 오래된 데이터 자동 삭제
- [ ] 집계 테이블 활용

### Phase 4: 대규모 (1M+ events/day)
- [ ] 데이터베이스 샤딩
- [ ] 읽기 전용 복제
- [ ] 별도 분석용 DB (ClickHouse, BigQuery)

---

## 📝 데이터 삭제 SQL 예제

### 수동 삭제 (90일 이상 된 데이터)
```sql
-- 삭제 전 개수 확인
SELECT COUNT(*) FROM analytics_events
WHERE created_at < datetime('now', '-90 days');

-- 백업 (선택사항)
CREATE TABLE analytics_events_archive AS
SELECT * FROM analytics_events
WHERE created_at < datetime('now', '-90 days');

-- 삭제
DELETE FROM analytics_events
WHERE created_at < datetime('now', '-90 days');

-- VACUUM (SQLite 용량 회수)
VACUUM;
```

### Python 스크립트
```python
from datetime import datetime, timedelta
from backend.database import SessionLocal
from backend.database.model import AnalyticsEvent

def cleanup_old_events(retention_days=90):
    db = SessionLocal()
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    deleted = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.created_at < cutoff_date
    ).delete()

    db.commit()
    print(f"Deleted {deleted} events older than {retention_days} days")
    db.close()

if __name__ == "__main__":
    cleanup_old_events(retention_days=90)
```

---

## 🚨 주의사항

1. **데이터 삭제 전 반드시 백업**
   - 실수로 중요 데이터 삭제 방지
   - S3, Google Cloud Storage 등 활용

2. **집계 후 삭제**
   - 집계 크론잡 도입 후에는 집계 완료 확인 후 삭제
   - 미집계 데이터 삭제 시 통계 손실

3. **인덱스 유지**
   - 대량 삭제 후 VACUUM/REINDEX 실행
   - 성능 저하 방지

4. **테스트 환경에서 먼저 검증**
   - 프로덕션 적용 전 스테이징에서 테스트
   - 삭제 로직 검증

---

## 📚 참고 자료

- APScheduler 문서: https://apscheduler.readthedocs.io/
- SQLAlchemy 인덱스: https://docs.sqlalchemy.org/en/20/core/constraints.html
- FastAPI 백그라운드 태스크: https://fastapi.tiangolo.com/tutorial/background-tasks/

---

## 🤝 문의

- 성능 이슈 발생 시: `backend/logs/backend.log` 확인
- 집계 시스템 도입 시점: 위 가이드 참고
- 추가 분석 기능 필요 시: `EventType` enum에 타입 추가
