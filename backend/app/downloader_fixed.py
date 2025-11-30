import os
import requests
import m3u8
import threading
import queue
import time
import json
import shutil
from urllib.parse import urljoin, urlparse
from Crypto.Cipher import AES
import hashlib
from typing import Optional, Dict, List, Callable
import tempfile
import logging
import subprocess
import sys
import random

logger = logging.getLogger(__name__)

class M3U8Downloader:
    """M3U8下载器 - 高性能版本"""
    
    def __init__(self, task_id: str, url: str, save_path: str, 
                 max_threads: int = 10,  # 默认改为10线程
                 cookies: Optional[Dict] = None, proxy: Optional[Dict] = None):
        self.task_id = task_id
        self.url = url
        self.save_path = save_path
        self.max_threads = min(max_threads, 20)  # 限制最大20线程
        self.is_stopped = False
        self.is_paused = False
        
        # 下载速度跟踪
        self.downloaded_bytes = 0
        self.start_time = time.time()
        self.current_speed = 0
        
        # AES 解密相关
        self.key = None
        self.iv = None
        
        # 创建会话 - 使用连接池和更优的配置
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,  # 减少连接数
            pool_maxsize=50,      # 减少最大连接
            max_retries=2
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 增强的通用 User-Agent 列表
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # 增强的防盗链域名配置
        self.domain_headers = {
            'modujx10.com': {
                'Referer': 'https://play.modujx10.com/',
                'Origin': 'https://play.modujx10.com'
            },
            'example.com': {
                'Referer': 'https://example.com/',
                'Origin': 'https://example.com'
            }
        }
        
        if cookies:
            self.session.cookies.update(cookies)
        if proxy:
            self.session.proxies.update(proxy)

    def _get_random_user_agent(self) -> str:
        """获取随机 User-Agent"""
        return random.choice(self.user_agents)

    def _get_domain_headers(self, url: str) -> Dict:
        """根据域名获取特定的请求头"""
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        for config_domain, config_headers in self.domain_headers.items():
            if config_domain in domain:
                headers.update(config_headers)
                break
        else:
            headers['Referer'] = f"{parsed_url.scheme}://{domain}/"
            headers['Origin'] = f"{parsed_url.scheme}://{domain}"
        
        return headers

    def _get_ffmpeg_path(self) -> Optional[str]:
        """获取FFmpeg路径"""
        if shutil.which('ffmpeg'):
            return 'ffmpeg'
        return None

    def download_with_retry(self, url: str, max_retries: int = 3, timeout: int = 15):
        """带重试的下载 - 增强防盗链支持"""
        for i in range(max_retries):
            if self.is_stopped:
                return None
                
            try:
                headers = self._get_domain_headers(url)
                
                start_time = time.time()
                resp = self.session.get(url, timeout=timeout, headers=headers)
                resp.raise_for_status()
                
                content = resp.content
                content_size = len(content)
                
                # 更新下载统计
                self.downloaded_bytes += content_size
                download_time = time.time() - start_time
                
                if download_time > 0:
                    self.current_speed = content_size / download_time
                
                return content
                
            except Exception as e:
                logger.warning(f"下载失败 (尝试 {i+1}/{max_retries}): {str(e)}")
                if i < max_retries - 1:
                    time.sleep(1)
                else:
                    raise
        return None

    def load_key(self, key_uri: str, base_uri: str):
        """加载AES密钥"""
        if not key_uri:
            return
            
        key_url = key_uri if key_uri.startswith('http') else urljoin(base_uri, key_uri)
        key_content = self.download_with_retry(key_url)
        if key_content:
            self.key = key_content
            print(f"✅ 密钥加载成功，长度: {len(key_content)} bytes")

    def decrypt_ts(self, data: bytes, segment) -> bytes:
        """解密TS分片"""
        if not self.key:
            return data
            
        # 获取IV
        if segment.key and segment.key.iv:
            iv = bytes.fromhex(segment.key.iv.replace("0x", ""))
        else:
            seq = getattr(segment, 'media_sequence', 0) or 0
            iv = seq.to_bytes(16, byteorder='big')
        
        # AES解密
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return cipher.decrypt(data)

    def download_segments(self, segments: List, base_uri: str, temp_dir: str, 
                         progress_callback: Optional[Callable] = None) -> bool:
        """下载分片 - 支持断点续传"""
        # 检查临时目录中已下载的文件
        existing_files = set()
        if os.path.exists(temp_dir):
            for f in os.listdir(temp_dir):
                if f.endswith('.ts') and f.replace('.ts', '').isdigit():
                    existing_files.add(int(f.replace('.ts', '')))
        
        task_queue = queue.Queue()
        
        # 只下载未完成的分片
        for i, segment in enumerate(segments):
            if i not in existing_files:
                filename = f"{i:05d}.ts"
                task_queue.put((i, segment, filename))
        
        total_segments = len(segments)
        downloaded_segments = len(existing_files)
        total_tasks = task_queue.qsize()
        
        if downloaded_segments > 0:
            print(f"🔄 发现 {downloaded_segments} 个已下载分片，继续下载剩余 {total_tasks} 个分片")
        
        completed_tasks = 0
        lock = threading.Lock()
        last_progress_update = 0
        
        def worker():
            nonlocal completed_tasks, last_progress_update
            while not self.is_stopped and not task_queue.empty():
                while self.is_paused and not self.is_stopped:
                    time.sleep(0.5)
                
                try:
                    i, segment, filename = task_queue.get(timeout=1)
                except queue.Empty:
                    break
                
                try:
                    seg_url = segment.absolute_uri or urljoin(base_uri, segment.uri)
                    ts_data = self.download_with_retry(seg_url)
                    
                    if ts_data:
                        if self.key:
                            ts_data = self.decrypt_ts(ts_data, segment)
                        
                        ts_path = os.path.join(temp_dir, filename)
                        with open(ts_path, 'wb') as f:
                            f.write(ts_data)
                        
                        with lock:
                            completed_tasks += 1
                            current_downloaded = downloaded_segments + completed_tasks
                            current_progress = (current_downloaded / total_segments) * 100
                            
                            if progress_callback:
                                speed_str = self._format_speed(self.current_speed)
                                progress_callback(current_progress, current_downloaded, total_segments, speed_str)
                            
                            if int(current_progress) > last_progress_update or completed_tasks % 5 == 0:
                                speed_str = self._format_speed(self.current_speed)
                                print(f"📊 进度: {current_progress:.1f}% ({current_downloaded}/{total_segments}), 速度: {speed_str}")
                                last_progress_update = int(current_progress)
                    
                except Exception as e:
                    logger.error(f"分片下载失败: {str(e)}")
                    task_queue.put((i, segment, filename))
                finally:
                    task_queue.task_done()
        
        # 限制实际线程数不超过剩余任务数
        actual_threads = min(self.max_threads, total_tasks, 20)
        threads = []
        for _ in range(actual_threads):
            t = threading.Thread(target=worker, daemon=True)
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()
        
        return not self.is_stopped and (completed_tasks > 0 or downloaded_segments == total_segments)

    def _format_speed(self, speed_bytes: float) -> str:
        """格式化速度显示"""
        if speed_bytes <= 0:
            return "0 B/s"
        
        if speed_bytes < 1024:
            return f"{speed_bytes:.1f} B/s"
        elif speed_bytes < 1024 * 1024:
            return f"{speed_bytes/1024:.1f} KB/s"
        else:
            return f"{speed_bytes/(1024*1024):.1f} MB/s"

    def merge_with_ffmpeg(self, ts_files: List[str], output_path: str) -> bool:
        """使用FFmpeg合并视频"""
        ffmpeg_path = self._get_ffmpeg_path()
        if not ffmpeg_path:
            logger.error("FFmpeg未找到")
            return False
        
        try:
            filelist_path = os.path.join(os.path.dirname(ts_files[0]), "filelist.txt")
            with open(filelist_path, 'w', encoding='utf-8') as f:
                for tf in ts_files:
                    f.write(f"file '{os.path.basename(tf)}'\n")
            
            cmd = [
                ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', filelist_path,
                '-c', 'copy',
                '-movflags', 'faststart',
                '-y',
                '-loglevel', 'quiet',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
                
        except Exception as e:
            logger.error(f"FFmpeg合并失败: {str(e)}")
            return False

    def download(self, progress_callback: Optional[Callable] = None, 
                status_callback: Optional[Callable] = None) -> bool:
        """主下载方法"""
        try:
            if status_callback:
                status_callback("解析M3U8文件...")
            
            print(f"🔗 开始处理URL: {self.url}")
            print(f"🎯 使用线程数: {self.max_threads}")
            
            # 初始化下载统计
            self.downloaded_bytes = 0
            self.start_time = time.time()
            self.current_speed = 0
            
            # 下载M3U8文件
            m3u8_content = self.download_with_retry(self.url)
            if not m3u8_content:
                raise Exception("无法下载M3U8文件")
            
            content_text = m3u8_content.decode('utf-8', errors='ignore')
            print(f"📄 M3U8内容类型: {'主播放列表' if '#EXT-X-STREAM-INF' in content_text else '媒体播放列表'}")
            
            # 解析M3U8
            playlist = m3u8.loads(content_text, uri=self.url)
            actual_url = self.url
            
            # 处理主播放列表
            if playlist.is_variant:
                if status_callback:
                    status_callback("选择最高质量流...")
                
                print("🎯 主播放列表信息:")
                for i, pl in enumerate(playlist.playlists):
                    resolution = getattr(pl.stream_info, 'resolution', '未知')
                    bandwidth = getattr(pl.stream_info, 'bandwidth', 0)
                    print(f"  {i+1}. 分辨率: {resolution}, 带宽: {bandwidth//1000}kbps")
                
                if playlist.playlists:
                    selected_playlist = playlist.playlists[0]
                    stream_url = selected_playlist.absolute_uri or urljoin(self.url, selected_playlist.uri)
                    print(f"🎬 选择流: {stream_url}")
                    
                    stream_content = self.download_with_retry(stream_url)
                    if not stream_content:
                        raise Exception("无法下载媒体流")
                    
                    playlist = m3u8.loads(stream_content.decode('utf-8', errors='ignore'), uri=stream_url)
                    actual_url = stream_url
                    print(f"✅ 媒体播放列表加载成功，包含 {len(playlist.segments)} 个分片")
                else:
                    raise Exception("主播放列表中无可用流")
            
            base_uri = playlist.base_uri or '/'.join(actual_url.split('/')[:-1]) + '/'
            if not base_uri.endswith('/'):
                base_uri += '/'
            
            segments = [seg for seg in playlist.segments if seg.uri]
            print(f"📊 有效分片数量: {len(segments)}")
            
            if not segments:
                raise Exception("无有效分片")
            
            # 处理加密
            if playlist.keys and any(k for k in playlist.keys if k):
                first_key = next(k for k in playlist.keys if k)
                print(f"🔐 检测到加密: {first_key.method}")
                self.load_key(first_key.uri, base_uri)
                if status_callback:
                    status_callback("处理加密...")
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix=f"m3u8_{self.task_id}_")
            
            try:
                # 下载分片
                if status_callback:
                    status_callback("下载分片...")
                
                print(f"🚀 开始下载 {len(segments)} 个分片，使用 {self.max_threads} 线程")
                success = self.download_segments(segments, base_uri, temp_dir, progress_callback)
                
                if not success:
                    raise Exception("下载被中止")
                
                # 合并视频
                if status_callback:
                    status_callback("合并视频...")
                
                ts_files = sorted([os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith('.ts')])
                print(f"📦 准备合并 {len(ts_files)} 个TS文件")
                
                if not ts_files:
                    raise Exception("无TS文件可合并")
                
                os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
                
                # 使用FFmpeg合并
                if not self.merge_with_ffmpeg(ts_files, self.save_path):
                    raise Exception("视频合并失败")
                
                if status_callback:
                    status_callback("下载完成")
                
                print("🎉 下载任务圆满完成!")
                return True
                
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"下载失败: {str(e)}")
            if status_callback:
                status_callback(f"失败: {str(e)}")
            return False
