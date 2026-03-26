"""
系统状态 API 路由
"""
from fastapi import APIRouter
from typing import Dict, Any

from ...ai_framework.engine_manager import get_engine_manager
from ...ai_framework.resource_monitor import get_resource_monitor
from ...ai_framework.model_registry import get_model_registry

router = APIRouter()


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    获取系统整体状态

    Returns:
        Dict: 系统状态信息
    """
    engine_manager = get_engine_manager()
    resource_monitor = get_resource_monitor()

    from ..server import _server_start_time
    import time
    uptime = time.time() - _server_start_time if _server_start_time > 0 else 0

    return {
        "api": {
            "status": "ok",
            "version": "1.0.0",
            "uptime_seconds": round(uptime),
        },
        "engine": engine_manager.health_check(),
        "resources": resource_monitor.get_full_status(),
    }


@router.get("/status/gpu")
async def get_gpu_status():
    """获取 GPU 状态"""
    monitor = get_resource_monitor()
    return monitor.get_gpu_status()


@router.get("/status/memory")
async def get_memory_status():
    """获取记忆库统计"""
    from ...memory.storage import get_memory_storage
    try:
        storage = get_memory_storage()
        stats = storage.get_stats()
        return {"enabled": True, **stats}
    except Exception:
        return {"enabled": False, "total_interactions": 0, "database_size_mb": 0}


@router.get("/status/models")
async def get_models_status():
    """获取模型列表"""
    registry = get_model_registry()
    models = registry.scan_models()

    loaded_model = registry.get_loaded_model()

    return {
        "total": len(models),
        "loaded": loaded_model.name if loaded_model else None,
        "models": [
            {
                "name": m.name,
                "size_gb": m.size_gb,
                "type": m.model_type,
                "is_loaded": m.is_loaded,
            }
            for m in models
        ]
    }
