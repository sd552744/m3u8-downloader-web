# M3U8 Downloader Web

一个基于 FastAPI + React 的 M3U8 视频下载器，支持多线程下载和自动合并。

## 功能特点

- 🚀 多线程下载 M3U8 视频
- 🔒 支持 AES 加密的 M3U8 链接
- 📦 自动合并 TS 分片为 MP4 文件
- 🎯 实时进度显示和下载速度监控
- ⏸️ 支持暂停、恢复下载任务
- 🗑️ 回收站和任务管理
- 🐳 Docker 容器化部署

## 技术栈
### 后端
- FastAPI
- SQLAlchemy
- SQLite
- Uvicorn
### 前端
- React
- TypeScript
- Material-UI
- Vite
## 快速开始
### 手动部署
#### 后端


## 快速开始
### 手动部署
#### 后端
cd backend
pip install -r requirements.txt
uvicorn app.main_fixed:app --host 0.0.0.0 --port 8000
#### 前端
cd frontend
npm install
npm run build # 将 dist/ 目录部署到 Web 服务器
### 使用 Docker 部署（推荐）
#### 1. 克隆项目：bash
git clone https://github.com/sd552744/m3u8-downloader-web.git
cd m3u8-downloader-web
#### 2. 启动服务：
docker-compose up -d
#### 3. 访问应用：
前端: http://localhost
API文档: http://localhost:8000/docs

## 项目结构
m3u8-downloader-web/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── main_fixed.py    # FastAPI 主应用
│   │   ├── downloader_fixed.py # M3U8 下载器
│   │   ├── models.py        # 数据模型
│   │   └── database.py      # 数据库配置
│   ├── Dockerfile.backend   # 后端 Dockerfile
│   └── requirements.txt     # Python 依赖
├── frontend/                # 前端代码
│   ├── src/                 # 源码目录
│   ├── dist/                # 构建输出
│   ├── package.json         # 前端依赖
│   └── Dockerfile.frontend  # 前端 Dockerfile
├── nginx/                   # Nginx 配置
├── docker-compose.yml       # Docker 编排
└── README.md               # 项目说明
## API 文档
启动服务后访问：http://localhost:8000/docs


