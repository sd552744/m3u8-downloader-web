#!/usr/bin/env python3
import requests
import m3u8
from urllib.parse import urljoin

def test_m3u8(url):
    print(f"🔍 测试 M3U8 URL: {url}")
    
    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://play.modujx10.com/',
        'Accept': '*/*',
    }
    
    try:
        # 下载 M3U8 文件
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📄 HTTP 状态码: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ M3U8 文件下载失败")
            return False
        
        content = response.text
        print(f"📝 文件大小: {len(content)} 字符")
        print(f"📋 内容预览:\n{content[:500]}...")
        
        # 解析 M3U8
        playlist = m3u8.loads(content, uri=url)
        
        print(f"🎯 M3U8 类型: {'主播放列表' if playlist.is_variant else '媒体播放列表'}")
        print(f"📊 分片数量: {len(playlist.segments)}")
        print(f"⏱️ 目标时长: {playlist.target_duration}")
        print(f"🔐 加密: {'是' if playlist.keys and any(playlist.keys) else '否'}")
        
        if playlist.is_variant:
            print("🌈 可用清晰度:")
            for i, pl in enumerate(playlist.playlists):
                resolution = getattr(pl.stream_info, 'resolution', '未知')
                bandwidth = getattr(pl.stream_info, 'bandwidth', 0)
                print(f"  {i+1}. 分辨率: {resolution}, 带宽: {bandwidth/1000:.0f}kbps")
                
                # 测试第一个分片
                if i == 0 and pl.uri:
                    stream_url = pl.absolute_uri or urljoin(url, pl.uri)
                    print(f"    测试流: {stream_url}")
                    test_stream(stream_url, headers)
        
        # 显示分片信息
        if playlist.segments:
            print("📦 分片信息 (前5个):")
            for i, seg in enumerate(playlist.segments[:5]):
                print(f"  {i+1}. URI: {seg.uri}")
                print(f"     时长: {seg.duration}")
                if seg.key:
                    print(f"     加密: 是, 方法: {seg.key.method}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_stream(stream_url, headers):
    try:
        response = requests.get(stream_url, headers=headers, timeout=10)
        print(f"    📄 流状态码: {response.status_code}")
        
        if response.status_code == 200:
            playlist = m3u8.loads(response.text, uri=stream_url)
            print(f"    📊 流分片数: {len(playlist.segments)}")
            
            if playlist.segments:
                # 测试第一个分片
                first_segment = playlist.segments[0]
                segment_url = first_segment.absolute_uri or urljoin(stream_url, first_segment.uri)
                seg_response = requests.get(segment_url, headers=headers, timeout=10, stream=True)
                print(f"    🔍 分片测试: {seg_response.status_code}, 大小: {len(seg_response.content)} bytes")
        else:
            print("    ❌ 流不可访问")
    except Exception as e:
        print(f"    ❌ 流测试失败: {str(e)}")

if __name__ == "__main__":
    url = "https://play.modujx10.com/20240309/NSKbMlxg/index.m3u8"
    test_m3u8(url)
