"""
日志 WebSocket 推送
"""
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

router = APIRouter()

# 存储活跃的 WebSocket 连接
_active_connections: List[WebSocket] = []


class LogHandler(logging.Handler):
    """自定义日志处理器，将日志发送到 WebSocket"""

    def emit(self, record):
        """日志记录时调用"""
        msg = self.format(record)
        # 异步发送到所有连接（仅在事件循环运行时）
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(broadcast_log(msg))
        except RuntimeError:
            # 非异步上下文（如推理线程），跳过 WebSocket 推送
            pass


def setup_log_handler():
    """设置日志处理器（防止重复添加）"""
    root_logger = logging.getLogger()

    # 检查是否已添加过 LogHandler，避免 reload 时重复
    if any(isinstance(h, LogHandler) for h in root_logger.handlers):
        return

    handler = LogHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


@router.websocket("/ws/logs")
async def logs_websocket(websocket: WebSocket):
    """
    日志 WebSocket 端点

    客户端连接后接收实时日志推送
    """
    await websocket.accept()
    _active_connections.append(websocket)

    try:
        # 保持连接
        while True:
            # 接收客户端消息（心跳等）
            data = await websocket.receive_text()

            # 处理客户端命令
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        _active_connections.remove(websocket)
        print(f"[WebSocket] 客户端断开连接")


async def broadcast_log(message: str):
    """
    广播日志到所有连接的客户端

    Args:
        message: 日志消息
    """
    if not _active_connections:
        return

    disconnected = []

    for connection in _active_connections:
        try:
            await connection.send_text(message)
        except Exception:
            # 连接已断开，标记移除
            disconnected.append(connection)

    # 移除断开的连接
    for connection in disconnected:
        if connection in _active_connections:
            _active_connections.remove(connection)


# 自动设置日志处理器
setup_log_handler()
