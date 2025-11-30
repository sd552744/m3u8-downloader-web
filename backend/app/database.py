from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
#from .models import Base
from models import Base
import os
import threading

# SQLite数据库 - 使用相对路径
#db_path = os.path.join(os.path.dirname(__file__), "..", "m3u8_downloader.db")
db_path = "/app/m3u8_downloader.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

# 创建线程安全的数据库引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=True  #开启日志便于调试
)

# 创建线程安全的session工厂
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine),
    scopefunc=threading.get_ident
)

def init_db():
    Base.metadata.create_all(bind=engine)
    print(f"✅ 数据库初始化完成，路径: {db_path}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        SessionLocal.remove()
