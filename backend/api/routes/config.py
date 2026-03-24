"""
配置管理 API 路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict

from app.config import config

router = APIRouter()


class ConfigUpdate(BaseModel):
    """配置更新请求"""
    path: str  # 配置路径，如 "engine.type"
    value: Any  # 新值


class ConfigBatchUpdate(BaseModel):
    """批量配置更新请求"""
    updates: list[ConfigUpdate]


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    """获取完整配置"""
    return config.all()


@router.get("/config/{path:path}")
async def get_config_value(path: str):
    """
    获取指定配置值

    Args:
        path: 配置路径，如 "engine/type"
    """
    keys = path.split('/')
    value = config.get(*keys, default=None)

    if value is None:
        return {"error": f"配置项未找到：{path}", "value": None}

    return {"path": path, "value": value}


@router.post("/config")
async def update_config(update: ConfigUpdate):
    """
    更新配置（仅内存，不保存到文件）

    Args:
        update: 更新请求
    """
    keys = update.path.split('.')
    success = config.set(*keys, value=update.value)

    if not success:
        return {"success": False, "error": "配置更新失败"}

    return {
        "success": True,
        "path": update.path,
        "value": update.value,
    }


@router.post("/config/batch")
async def batch_update_config(batch: ConfigBatchUpdate):
    """批量更新配置"""
    results = []
    for update in batch.updates:
        keys = update.path.split('.')
        success = config.set(*keys, value=update.value)
        results.append({"path": update.path, "success": success})

    all_success = all(r["success"] for r in results)
    return {
        "success": all_success,
        "results": results,
    }


@router.post("/config/reload")
async def reload_config():
    """重新从文件加载配置（会覆盖内存中的修改）"""
    success = config.reload()
    return {
        "success": success,
        "message": "配置已重新加载" if success else "配置重新加载失败"
    }


@router.post("/config/save")
async def save_config():
    """保存当前配置到文件"""
    success = config.save()
    return {
        "success": success,
        "message": "配置已保存" if success else "配置保存失败"
    }
