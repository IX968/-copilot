"""
FastAPI 服务器
提供 REST API 和 WebSocket 接口
"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import config


# ======================
# 静态文件挂载
# ======================

def mount_static_files(application: FastAPI):
    """挂载静态文件目录（逐个检查子目录是否存在）"""
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"

    if not frontend_dir.exists():
        print("[API Server] 前端目录不存在，跳过静态文件挂载")
        return

    css_dir = frontend_dir / "css"
    if css_dir.exists():
        application.mount("/css", StaticFiles(directory=str(css_dir)), name="css")

    js_dir = frontend_dir / "js"
    if js_dir.exists():
        application.mount("/js", StaticFiles(directory=str(js_dir)), name="js")

    assets_dir = frontend_dir / "assets"
    if assets_dir.exists():
        application.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


# ======================
# 生命周期管理
# ======================

@asynccontextmanager
async def lifespan(application: FastAPI):
    """服务器生命周期管理"""
    print("[API Server] 启动中...")

    # 挂载静态文件
    mount_static_files(application)

    # 导入并注册路由
    from .routes import status, models, generate, config as config_routes

    application.include_router(status.router, prefix="/api", tags=["状态"])
    application.include_router(models.router, prefix="/api/models", tags=["模型"])
    application.include_router(generate.router, prefix="/api", tags=["生成"])
    application.include_router(config_routes.router, prefix="/api", tags=["配置"])

    # WebSocket 路由
    from .websocket import logs as logs_ws
    application.include_router(logs_ws.router)

    print("[API Server] 启动完成")
    print(f"[API Server] API 文档：http://{config.get('server', 'host')}:{config.get('server', 'port')}/api/docs")

    yield  # 应用运行期间

    # 关闭清理
    print("[API Server] 关闭中...")


# ======================
# 创建 FastAPI 应用
# ======================

app = FastAPI(
    title="Global AI Copilot API",
    description="本地 AI 补全服务的 API 接口",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# 添加 CORS 中间件（允许本地前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本地开发，允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ======================
# 根路径
# ======================

@app.get("/", response_class=HTMLResponse)
async def root():
    """返回前端主页面"""
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    index_path = frontend_dir / "index.html"

    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        return HTMLResponse(
            content="<h1>Global AI Copilot API</h1><p>访问 <a href='/api/docs'>/api/docs</a> 查看 API 文档</p>",
            status_code=200
        )


# ======================
# 健康检查
# ======================

@app.get("/api/health")
async def health_check():
    """API 健康检查"""
    return {"status": "ok", "version": "1.0.0"}


# ======================
# 启动入口
# ======================

def start_server(host: str = None, port: int = None, reload: bool = False):
    """
    启动 API 服务器

    Args:
        host: 监听地址
        port: 监听端口
        reload: 是否启用热重载（开发模式）
    """
    host = host or config.get('server', 'host', default='127.0.0.1')
    port = port or config.get('server', 'port', default=7891)
    reload = reload or config.get('server', 'reload', default=False)

    print(f"[API Server] 准备启动：http://{host}:{port}")

    uvicorn.run(
        "backend.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    start_server()
