from sqlalchemy.orm import Session
from backend.database.database import database
from backend.database.model import User, Tag
from backend.database.dao.user_dao import UserDAO

def init_database():
    """데이터베이스를 초기화하고 기본 데이터를 생성합니다."""
    # 테이블 생성
    database.create_tables()
    
    # 세션 생성
    db = next(database.get_db())
    
    try:
        # 기본 관리자 계정 생성
        user_dao = UserDAO(db)
        
        # 관리자 계정이 없으면 생성
        admin = user_dao.get_user_by_username("admin")
        if not admin:
            admin = user_dao.create_user(
                username="admin",
                email="admin@smithery.com",
                password="admin123",
                is_admin="admin"
            )
            print(f"관리자 계정이 생성되었습니다: {admin.username}")
        
        # 기본 태그 생성
        default_tags = [
            "AI", "Automation", "Productivity", "Development", "Tools",
            "API", "Integration", "Data", "Analysis", "Machine Learning"
        ]
        
        for tag_name in default_tags:
            existing_tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not existing_tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                print(f"기본 태그가 생성되었습니다: {tag_name}")
        
        db.commit()
        print("데이터베이스 초기화가 완료되었습니다.")
        
    except Exception as e:
        print(f"데이터베이스 초기화 중 오류가 발생했습니다: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database() 