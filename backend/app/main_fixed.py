from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
import uuid
import os
from datetime import datetime, timedelta
import threading
import time
import schedule
import glob
from sqlalchemy.orm import Session

#from .downloader_fixed import M3U8Downloader
#from .models import DownloadTask, TaskStatus
#from .database import get_db, init_db, SessionLocal
from downloader_fixed import M3U8Downloader
from models import DownloadTask, TaskStatus
from database import get_db, init_db, SessionLocal

app = FastAPI(title="M3U8 Downloader - Enhanced Version", version="1.5.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量控制最大并发任务数 - 改为5个，最大10个
MAX_CONCURRENT_TASKS = 5
MAX_CONCURRENT_TASKS_LIMIT = 10
active_tasks: Dict[str, M3U8Downloader] = {}
pending_tasks: List[str] = []
task_lock = threading.Lock()

# 数据库初始化
@app.on_event("startup")
async def startup_event():
    init_db()
    os.makedirs("./downloads", exist_ok=True)
    print("✅ 数据库初始化完成")
    print("✅ 下载目录创建完成")
    print("🚀 使用增强版本下载器")
    print(f"🎯 最大并发任务数: {MAX_CONCURRENT_TASKS} (可配置最大{MAX_CONCURRENT_TASKS_LIMIT})")
    print(f"🎯 默认线程数: 10 (可配置最大20)")
    
    cleanup_thread = threading.Thread(target=run_scheduler, daemon=True)
    cleanup_thread.start()
    print("✅ 定时清理任务已启动")

def run_scheduler():
    """运行定时任务调度器"""
    schedule.every().day.at("03:00").do(cleanup_old_files_task)
    schedule.every(6).hours.do(cleanup_old_files_task)
    
    print("🕒 定时清理任务安排: 每天03:00和每6小时执行一次")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except Exception as e:
            print(f"❌ 定时任务执行错误: {str(e)}")
            time.sleep(300)

def cleanup_old_files_task():
    """定时清理旧文件"""
    try:
        print(f"🧹 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始定时清理任务...")
        
        db = SessionLocal()
        try:
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            old_tasks = db.query(DownloadTask).filter(
                DownloadTask.status == TaskStatus.COMPLETED,
                DownloadTask.updated_at < seven_days_ago
            ).all()
            
            deleted_count = 0
            for task in old_tasks:
                file_path = os.path.join("./downloads", task.filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        task.status = TaskStatus.DELETED
                        deleted_count += 1
                        print(f"   🗑️ 自动清理文件: {task.filename}")
                    except Exception as e:
                        print(f"   ❌ 清理文件失败 {task.filename}: {str(e)}")
            
            db.commit()
            
            deleted_records = db.query(DownloadTask).filter(
                DownloadTask.status == TaskStatus.DELETED
            ).delete()
            db.commit()
            
            print(f"✅ 定时清理完成: 删除 {deleted_count} 个文件, 清理 {deleted_records} 条记录")
        finally:
            db.close()
        
    except Exception as e:
        print(f"❌ 定时清理任务失败: {str(e)}")

def start_next_pending_task():
    """启动下一个等待任务"""
    with task_lock:
        if pending_tasks and len(active_tasks) < MAX_CONCURRENT_TASKS:
            next_task_id = pending_tasks.pop(0)
            db = SessionLocal()
            try:
                task = db.query(DownloadTask).filter(DownloadTask.task_id == next_task_id).first()
                if task:
                    request = DownloadRequest(
                        url=task.url,
                        filename=task.filename,
                        max_threads=task.max_threads
                    )
                    thread = threading.Thread(
                        target=run_download_task,
                        args=(next_task_id, request),
                        daemon=True
                    )
                    thread.start()
                    task.status = TaskStatus.DOWNLOADING
                    db.commit()
                    print(f"🚀 从队列启动任务: {next_task_id}")
            finally:
                db.close()

class DownloadRequest(BaseModel):
    url: str
    filename: str
    max_threads: int = 10  # 默认改为10线程

class ConcurrencyUpdateRequest(BaseModel):
    max_tasks: int

class TaskResponse(BaseModel):
    task_id: str
    status: str
    progress: float
    filename: str
    created_at: str
    file_size: Optional[str] = None
    download_speed: Optional[str] = None
    error_message: Optional[str] = None

def update_task_progress(task_id: str, progress: float, status: TaskStatus = None, 
                        error_message: str = None, download_speed: str = None):
    """安全地更新任务进度和速度"""
    try:
        db = SessionLocal()
        try:
            task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
            if task:
                task.progress = progress
                if status:
                    task.status = status
                if error_message:
                    task.error_message = error_message
                if download_speed:
                    task.download_speed = download_speed
                db.commit()
        finally:
            db.close()
    except Exception as e:
        print(f"❌ 更新任务进度失败: {str(e)}")

def run_download_task(task_id: str, request: DownloadRequest):
    """在后台线程中运行下载任务"""
    try:
        with task_lock:
            if task_id in pending_tasks:
                pending_tasks.remove(task_id)
        
        update_task_progress(task_id, 0, TaskStatus.DOWNLOADING)
        
        save_path = os.path.join("./downloads", request.filename)
        
        print(f"🚀 开始下载任务: {task_id}, 线程数: {request.max_threads}")
        
        downloader = M3U8Downloader(
            task_id=task_id,
            url=request.url,
            save_path=save_path,
            max_threads=min(request.max_threads, 20)  # 限制最大20线程
        )
        
        with task_lock:
            active_tasks[task_id] = downloader
        
        def progress_callback(progress, current, total, speed):
            update_task_progress(task_id, progress, download_speed=speed)
        
        def status_callback(status):
            print(f"🔄 任务 {task_id} 状态: {status}")
        
        success = downloader.download(progress_callback, status_callback)
        
        if success:
            update_task_progress(task_id, 100, TaskStatus.COMPLETED, download_speed=None)
            if os.path.exists(save_path):
                size = os.path.getsize(save_path)
                db = SessionLocal()
                try:
                    task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
                    if task:
                        task.file_size = f"{size / 1024 / 1024:.1f}MB"
                        db.commit()
                finally:
                    db.close()
            print(f"✅ 任务 {task_id} 下载完成")
        else:
            update_task_progress(task_id, 0, TaskStatus.FAILED, "下载失败")
            print(f"❌ 任务 {task_id} 下载失败")
        
    except Exception as e:
        update_task_progress(task_id, 0, TaskStatus.FAILED, str(e))
        print(f"💥 任务 {task_id} 发生错误: {str(e)}")
    finally:
        with task_lock:
            active_tasks.pop(task_id, None)
        start_next_pending_task()

@app.post("/api/tasks", response_model=TaskResponse)
async def create_download_task(request: DownloadRequest, background_tasks: BackgroundTasks):
    """创建下载任务"""
    task_id = str(uuid.uuid4())[:8]
    
    print(f"📝 创建新任务: {task_id}, 线程数: {request.max_threads}")
    
    db = SessionLocal()
    try:
        task = DownloadTask(
            task_id=task_id,
            url=request.url,
            filename=request.filename,
            max_threads=min(request.max_threads, 20),  # 限制最大20线程
            status=TaskStatus.PENDING
        )
        
        db.add(task)
        db.commit()
        
        # 检查并发限制
        with task_lock:
            if len(active_tasks) >= MAX_CONCURRENT_TASKS:
                pending_tasks.append(task_id)
                task.status = TaskStatus.QUEUED
                db.commit()
                print(f"⏳ 任务 {task_id} 进入等待队列 (活跃: {len(active_tasks)}, 等待: {len(pending_tasks)})")
            else:
                thread = threading.Thread(
                    target=run_download_task,
                    args=(task_id, request),
                    daemon=True
                )
                thread.start()
        
        return TaskResponse(
            task_id=task_id,
            status=task.status.value,
            progress=0.0,
            filename=task.filename,
            created_at=task.created_at.isoformat()
        )
    finally:
        db.close()

@app.get("/api/files/{task_id}/download")
async def download_file(task_id: str):
    """下载文件到客户端"""
    db = SessionLocal()
    try:
        task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
        
        if not task or task.status != TaskStatus.COMPLETED:
            raise HTTPException(status_code=404, detail="文件不存在或未完成下载")
        
        file_path = os.path.join("./downloads", task.filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=file_path,
            filename=task.filename,
            media_type='application/octet-stream'
        )
    finally:
        db.close()

@app.delete("/api/files/{task_id}")
async def delete_file(task_id: str):
    """删除服务器上的文件（软删除到回收站）"""
    try:
        db = SessionLocal()
        try:
            task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
            
            if not task:
                raise HTTPException(status_code=404, detail="任务不存在")
            
            task.status = TaskStatus.DELETED
            db.commit()
            
            print(f"🗑️ 任务 {task_id} 已移到回收站")
            return {"message": "文件已移到回收站"}
        finally:
            db.close()
    except Exception as e:
        print(f"❌ 删除文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")
        
@app.post("/api/tasks/{task_id}/restore")
async def restore_task(task_id: str):
    """还原回收站中的任务"""
    db = SessionLocal()
    try:
        task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task.status != TaskStatus.DELETED:
            raise HTTPException(status_code=400, detail="任务不在回收站中")
        
        if task.progress == 100:
            task.status = TaskStatus.COMPLETED
        else:
            task.status = TaskStatus.PAUSED
        
        db.commit()
        
        print(f"♻️ 任务 {task_id} 已还原")
        return {"message": "任务已还原"}
    finally:
        db.close()

@app.post("/api/system/cleanup-all")
async def cleanup_all_files():
    """清理所有下载文件和缓存"""
    try:
        db = SessionLocal()
        try:
            download_dir = "./downloads"
            deleted_files = 0
            if os.path.exists(download_dir):
                for filename in os.listdir(download_dir):
                    file_path = os.path.join(download_dir, filename)
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            deleted_files += 1
                            print(f"🗑️ 清理文件: {filename}")
                        except Exception as e:
                            print(f"❌ 清理文件失败 {filename}: {str(e)}")
            
            deleted_records = db.query(DownloadTask).delete()
            db.commit()
            
            with task_lock:
                active_tasks.clear()
                pending_tasks.clear()
            
            return {
                "message": "清理完成",
                "deleted_files": deleted_files,
                "deleted_records": deleted_records
            }
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")

@app.get("/api/system/cleanup")
async def cleanup_old_files():
    """手动清理7天前的文件"""
    try:
        cleanup_old_files_task()
        return {"message": "手动清理完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")

@app.get("/api/tasks", response_model=List[TaskResponse])
async def get_tasks(limit: int = 100):
    """获取任务列表"""
    try:
        db = SessionLocal()
        try:
            tasks = db.query(DownloadTask).order_by(DownloadTask.created_at.desc()).limit(limit).all()
            
            return [
                TaskResponse(
                    task_id=task.task_id,
                    status=task.status.value,
                    progress=task.progress,
                    filename=task.filename,
                    created_at=task.created_at.isoformat(),
                    file_size=task.file_size,
                    download_speed=task.download_speed,
                    error_message=task.error_message
                )
                for task in tasks
            ]
        finally:
            db.close()
    except Exception as e:
        print(f"❌ 获取任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取任务列表失败")

@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """获取任务详情"""
    db = SessionLocal()
    try:
        task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return TaskResponse(
            task_id=task.task_id,
            status=task.status.value,
            progress=task.progress,
            filename=task.filename,
            created_at=task.created_at.isoformat(),
            file_size=task.file_size,
            download_speed=task.download_speed,
            error_message=task.error_message
        )
    finally:
        db.close()

@app.post("/api/tasks/{task_id}/pause")
async def pause_task(task_id: str):
    """暂停任务"""
    downloader = active_tasks.get(task_id)
    if downloader:
        downloader.is_paused = True
        update_task_progress(task_id, downloader.progress if hasattr(downloader, 'progress') else 0, TaskStatus.PAUSED)
        print(f"⏸️ 任务 {task_id} 已暂停")
    return {"message": "任务已暂停"}

@app.post("/api/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    """恢复任务"""
    db = SessionLocal()
    try:
        task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task.status != TaskStatus.PAUSED:
            raise HTTPException(status_code=400, detail="任务不是暂停状态")
        
        if task_id in active_tasks:
            downloader = active_tasks[task_id]
            downloader.is_paused = False
            task.status = TaskStatus.DOWNLOADING
            db.commit()
            print(f"▶️ 任务 {task_id} 已恢复")
            return {"message": "任务已恢复"}
        
        if task.progress < 100:
            with task_lock:
                if len(active_tasks) >= MAX_CONCURRENT_TASKS:
                    pending_tasks.append(task_id)
                    task.status = TaskStatus.QUEUED
                    db.commit()
                    print(f"⏳ 任务 {task_id} 进入等待队列 (活跃: {len(active_tasks)}, 等待: {len(pending_tasks)})")
                    return {"message": "任务已加入队列等待"}
                else:
                    request = DownloadRequest(
                        url=task.url,
                        filename=task.filename,
                        max_threads=task.max_threads
                    )
                    
                    thread = threading.Thread(
                        target=run_download_task,
                        args=(task_id, request),
                        daemon=True
                    )
                    thread.start()
                    
                    task.status = TaskStatus.DOWNLOADING
                    db.commit()
                    print(f"🚀 任务 {task_id} 重新开始下载")
                    return {"message": "任务已开始下载"}
        
        task.status = TaskStatus.DOWNLOADING
        db.commit()
        print(f"▶️ 任务 {task_id} 已恢复")
        return {"message": "任务已恢复"}
    finally:
        db.close()
    
@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """永久删除任务（从回收站中删除）"""
    downloader = active_tasks.get(task_id)
    if downloader:
        downloader.is_stopped = True
    
    db = SessionLocal()
    try:
        task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
        if task:
            file_path = os.path.join("./downloads", task.filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"🗑️ 已删除文件: {file_path}")
                except Exception as e:
                    print(f"❌ 删除文件失败: {str(e)}")
            
            db.delete(task)
            db.commit()
        
        print(f"🗑️ 任务 {task_id} 已永久删除")
        return {"message": "任务已永久删除"}
    finally:
        db.close()

@app.post("/api/system/update-concurrency")
async def update_concurrency(request: ConcurrencyUpdateRequest):
    """更新最大并发任务数"""
    global MAX_CONCURRENT_TASKS
    if request.max_tasks < 1 or request.max_tasks > MAX_CONCURRENT_TASKS_LIMIT:
        raise HTTPException(status_code=400, detail=f"并发任务数必须在1-{MAX_CONCURRENT_TASKS_LIMIT}之间")
    
    MAX_CONCURRENT_TASKS = request.max_tasks
    print(f"🔄 更新最大并发任务数为: {MAX_CONCURRENT_TASKS}")
    
    # 尝试启动等待的任务
    start_next_pending_task()
    
    return {"message": f"并发任务数已更新为 {MAX_CONCURRENT_TASKS}"}

@app.get("/api/system/info")
async def get_system_info():
    """获取系统信息"""
    import shutil
    
    db = SessionLocal()
    try:
        download_dir = "./downloads"
        total_size = 0
        file_count = 0
        if os.path.exists(download_dir):
            for file in os.listdir(download_dir):
                file_path = os.path.join(download_dir, file)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
                    file_count += 1
        
        return {
            "version": "1.5.0",
            "status": "running",
            "download_dir": download_dir,
            "file_count": file_count,
            "disk_usage": f"{total_size / 1024 / 1024:.1f}MB",
            "next_cleanup": "每天03:00",
            "max_concurrent_tasks": MAX_CONCURRENT_TASKS,
            "max_concurrent_limit": MAX_CONCURRENT_TASKS_LIMIT,
            "default_threads": 10,
            "max_threads": 20
        }
    finally:
        db.close()

@app.get("/")
async def root():
    return {
        "message": "🎬 M3U8 Downloader Web API - Enhanced Version", 
        "version": "1.5.0",
        "docs": "/docs",
        "endpoints": {
            "创建任务": "POST /api/tasks",
            "获取任务": "GET /api/tasks",
            "下载文件": "GET /api/files/{id}/download",
            "删除文件": "DELETE /api/files/{id}",
            "还原文件": "POST /api/tasks/{id}/restore",
            "系统信息": "GET /api/system/info",
            "手动清理": "GET /api/system/cleanup",
            "清理所有": "POST /api/system/cleanup-all",
            "更新并发": "POST /api/system/update-concurrency"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
