from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class TaskStatus(enum.Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"
    DELETED = "deleted"
    QUEUED = "queued"

class DownloadTask(Base):
    __tablename__ = "download_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(8), unique=True, index=True, nullable=False)
    url = Column(Text, nullable=False)
    filename = Column(String(255), nullable=False)
    max_threads = Column(Integer, default=10)  # 默认改为10线程
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    progress = Column(Float, default=0.0)
    file_size = Column(String(50))
    download_speed = Column(String(50))
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
